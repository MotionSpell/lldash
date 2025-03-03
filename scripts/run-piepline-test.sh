#!/bin/bash
set -e

# Kill processes on exit
trap 'kill $(jobs -p) 2>/dev/null || true' EXIT

if [ -n "$GITHUB_WORKSPACE" ]; then
  # GitHub Actions environment
  echo "Setting up CI environment..."
  
  export LD_LIBRARY_PATH=/usr/local/lib:$GITHUB_WORKSPACE/build/vcpkg_installed/x64-linux-dynamic/lib:$LD_LIBRARY_PATH
  export SIGNALS_SMD_PATH=$GITHUB_WORKSPACE/build/lib
  BINARY_PATH=$GITHUB_WORKSPACE/build/bin

  # Verify library paths are visible
  echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
  ldconfig -p | grep cwipc || echo "No CWIPC libraries in ldconfig cache"
else
  # Local environment - check if we're in the lldash repository root
  if [ ! -d "./build" ] || [ ! -d "./scripts" ]; then
    echo "Error: This script must be run from the lldash repository root directory"
    echo "Please run: cd /path/to/lldash && ./scripts/run-piepline-test.sh"
    exit 1
  fi
  
  # Use relative paths
  export LD_LIBRARY_PATH=./build/vcpkg_installed/x64-linux-dynamic/lib:$LD_LIBRARY_PATH
  export SIGNALS_SMD_PATH=./build/lib
  BINARY_PATH=./build/bin
fi

# Create temp files for output
SERVER_OUTPUT=$(mktemp)
CLIENT_OUTPUT=$(mktemp)
EVANESCENT_OUTPUT=$(mktemp)
TEST_FAILED=0

# Start evanescent server
echo "Starting evanescent server..."
${BINARY_PATH}/evanescent.exe --port 9000 > $EVANESCENT_OUTPUT 2>&1 &
SERVER_PID=$!
sleep 2

# Start cwipc_forward
echo "Starting cwipc_forward..."
( cwipc_forward --synthetic --nodrop --bin2dash http://127.0.0.1:9000/ > $SERVER_OUTPUT 2>&1 ) &
FORWARD_PID=$!

# Wait for MPD file to be ready
echo "Waiting for MPD file to be ready..."
MPD_READY=false
TIMEOUT=60
START_TIME=$(date +%s)

while [ $(($(date +%s) - START_TIME)) -lt $TIMEOUT ]; do
    if grep -q "Added.*bin2dashSink.mpd" $EVANESCENT_OUTPUT; then
        MPD_READY=true
        echo "MPD file is ready after $(($(date +%s) - START_TIME)) seconds"
        break
    fi
    # Print dots to show progress but reduce log volume
    sleep 1
    echo -n "."
    
    # Only print status every 20 seconds in CI to reduce log volume
    if [ -n "$GITHUB_WORKSPACE" ] && [ $(( ($(date +%s) - START_TIME) % 20 )) -eq 0 ]; then
        echo -e "\nWaiting for MPD file... ($(($(date +%s) - START_TIME)) seconds elapsed)"
    fi
done
echo ""

if [ "$MPD_READY" = false ]; then
    echo "Timed out waiting for MPD file"
    echo -e "\nDiagnostic checks:"
    echo "1. Checking if evanescent.exe is responsive:"
    curl -I http://127.0.0.1:9000/ || echo "Server not responding"
    
    echo "2. Checking cwipc_forward process status:"
    ps -p $FORWARD_PID -o state,cmd || echo "Process not running"
    
    exit 1
fi

# Wait for MPD to be fully processed
sleep 3

# Run client with explicit output capture
echo "Starting cwipc_view (will run for 30 seconds)..."
( cwipc_view --nodisplay --sub "http://127.0.0.1:9000/bin2dashSink.mpd" > $CLIENT_OUTPUT 2>&1 ) &
CLIENT_PID=$!

# Let them run for 30 seconds
echo "Running test for 30 seconds..."
sleep 30

# Send SIGINT to both processes to get statistics
echo "Sending SIGINT to get statistics..."
kill -SIGINT $CLIENT_PID || true
echo "Waiting 10 seconds for client statistics to print..."
sleep 10  # Increase wait time for statistics to print

kill -SIGINT $FORWARD_PID || true
echo "Waiting 10 seconds for server statistics to print..."
sleep 10  # Increase wait time for statistics to print

# Check for statistics output
echo "Checking for statistics output..."
echo "Server output has $(wc -l < $SERVER_OUTPUT) lines"
echo "Client output has $(wc -l < $CLIENT_OUTPUT) lines"

# Check if statistics are present
if ! grep -q "capture_duration" $SERVER_OUTPUT; then
    echo "No server statistics found. Showing last 20 lines:"
    tail -20 $SERVER_OUTPUT
    TEST_FAILED=1
fi

if ! grep -q "capture_duration" $CLIENT_OUTPUT; then
    echo "No client statistics found. Showing last 20 lines:"
    tail -20 $CLIENT_OUTPUT
    TEST_FAILED=1
fi

# Extract and compare statistics
echo -e "\nExtracted Statistics:"

# Server frame count
SERVER_FRAMES=$(grep "grab: capture_duration" $SERVER_OUTPUT | grep -o "count=[0-9]*" | cut -d= -f2)
echo "Server processed frames: ${SERVER_FRAMES:-N/A}"

# Client frame count
CLIENT_FRAMES=$(grep "grab: capture_duration" $CLIENT_OUTPUT | grep -o "count=[0-9]*" | cut -d= -f2)
echo "Client received frames: ${CLIENT_FRAMES:-N/A}"

# Compare if both values are available
if [ -n "$SERVER_FRAMES" ] && [ -n "$CLIENT_FRAMES" ]; then
    RATIO=$(echo "scale=2; 100 * $CLIENT_FRAMES / $SERVER_FRAMES" | bc)
    echo "Client received $RATIO% of server frames"
    
    if (( $(echo "$RATIO > 70" | bc -l) )); then
        echo "✅ Test PASSED: Client received more than 70% of frames"
    else
        echo "❌ Test FAILED: Client received less than 70% of frames"
        TEST_FAILED=1
    fi
else
    echo "❌ Test FAILED: Unable to compare frame counts"
    TEST_FAILED=1
fi

# Check server bandwidth vs client received bandwidth
SERVER_PACKET_SIZE=$(grep "bin2dash: packetsize" $SERVER_OUTPUT | grep -o "average=[0-9.]*" | cut -d= -f2)
CLIENT_PACKET_SIZE=$(grep "source_sub: packetsize" $CLIENT_OUTPUT | grep -o "average=[0-9.]*" | cut -d= -f2)

if [ -n "$SERVER_PACKET_SIZE" ] && [ -n "$CLIENT_PACKET_SIZE" ]; then
    echo "Server packet size: $SERVER_PACKET_SIZE bytes"
    echo "Client packet size: $CLIENT_PACKET_SIZE bytes"
    
    PACKET_RATIO=$(echo "scale=2; 100 * $CLIENT_PACKET_SIZE / $SERVER_PACKET_SIZE" | bc)
    echo "Client received $PACKET_RATIO% of packet data"
    
    if (( $(echo "$PACKET_RATIO > 95" | bc -l) )); then
        echo "✅ Test PASSED: Data integrity maintained (>95%)"
    else
        echo "❌ Test FAILED: Potential data loss (<95%)"
        TEST_FAILED=1
    fi
fi

# Generate test summary
echo -e "\n==== TEST SUMMARY ===="
if [ $TEST_FAILED -eq 0 ]; then
    echo "🟢 OVERALL TEST STATUS: PASSED"
else
    echo "🔴 OVERALL TEST STATUS: FAILED"
fi

echo -e "\nServer Stats:"
echo "- Processed frames: ${SERVER_FRAMES:-N/A}"
SERVER_ENCODE=$(grep "encode_duration" $SERVER_OUTPUT | grep -o "average=[0-9.]*" | cut -d= -f2)
echo "- Average encode time: ${SERVER_ENCODE:-N/A} sec"
echo "- Average packet size: ${SERVER_PACKET_SIZE:-N/A} bytes"

echo -e "\nClient Stats:"
echo "- Received frames: ${CLIENT_FRAMES:-N/A}"
echo "- Average packet size: ${CLIENT_PACKET_SIZE:-N/A} bytes"
CLIENT_LATENCY=$(grep "capture_latency" $CLIENT_OUTPUT | grep -o "average=[0-9.]*" | cut -d= -f2)
echo "- Average latency: ${CLIENT_LATENCY:-N/A} sec"
CLIENT_BANDWIDTH=$(grep "bandwidth" $CLIENT_OUTPUT | grep -o "average=[0-9.]*" | cut -d= -f2)
if [ -n "$CLIENT_BANDWIDTH" ]; then
    BANDWIDTH_MBPS=$(echo "scale=2; $CLIENT_BANDWIDTH / 1000000" | bc)
    echo "- Average bandwidth: $BANDWIDTH_MBPS Mbps"
else
    echo "- Average bandwidth: N/A"
fi

echo -e "\nComparison:"
[ -n "$RATIO" ] && echo "- Frame delivery rate: $RATIO%" || echo "- Frame delivery rate: N/A"
[ -n "$PACKET_RATIO" ] && echo "- Data integrity rate: $PACKET_RATIO%" || echo "- Data integrity rate: N/A"
echo "====================\n"

echo -e "\nTest complete."

# Cleanup
rm $SERVER_OUTPUT $CLIENT_OUTPUT $EVANESCENT_OUTPUT

# Exit with proper code for CI
exit $TEST_FAILED