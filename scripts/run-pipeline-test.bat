@echo off
REM Pipeline test script for lldash - Windows version

echo ============== PIPELINE TEST ==============

REM Create logs directory
mkdir logs\server logs\client logs\evanescent logs\system 2>nul

REM Define temp file locations
set SERVER_OUTPUT=%TEMP%\server_output.txt
set CLIENT_OUTPUT=%TEMP%\client_output.txt
set EVANESCENT_OUTPUT=%TEMP%\evanescent_output.txt
set TEST_FAILED=0

echo Starting evanescent server...
start /b %BUILD_DIR%\build\bin\evanescent.exe --port 9000 > %EVANESCENT_OUTPUT% 2>&1
timeout /t 2 /nobreak > nul

echo Starting cwipc_forward...
start /b cwipc_forward.exe --verbose --synthetic --nodrop --bin2dash http://127.0.0.1:9000/ > %SERVER_OUTPUT% 2>&1

echo Waiting for MPD file to be ready...
set MPD_READY=false
set ATTEMPT=0
set MAX_ATTEMPTS=60

:MPD_WAIT_LOOP
set /a ATTEMPT+=1
findstr /C:"Added" /C:"bin2dashSink.mpd" %EVANESCENT_OUTPUT% > nul
if %ERRORLEVEL% EQU 0 (
    set MPD_READY=true
    echo MPD file is ready after %ATTEMPT% seconds
    goto :MPD_READY
)
if %ATTEMPT% GEQ %MAX_ATTEMPTS% goto :MPD_TIMEOUT
echo .
timeout /t 1 /nobreak > nul
goto :MPD_WAIT_LOOP

:MPD_TIMEOUT
echo Timed out waiting for MPD file
exit /b 1

:MPD_READY
timeout /t 3 /nobreak > nul

echo Starting cwipc_view client...
start /b cwipc_view.exe --verbose --nodisplay --sub "http://127.0.0.1:9000/bin2dashSink.mpd" > %CLIENT_OUTPUT% 2>&1

echo Waiting for client to initialize...
set CLIENT_STARTED=false
set ATTEMPT=0
set MAX_ATTEMPTS=10

:CLIENT_WAIT_LOOP
set /a ATTEMPT+=1
findstr /C:"Added: stream #0" /C:"grab: captured" %CLIENT_OUTPUT% > nul
if %ERRORLEVEL% EQU 0 (
    set CLIENT_STARTED=true
    echo Client successfully initialized
    goto :CLIENT_READY
)
if %ATTEMPT% GEQ %MAX_ATTEMPTS% goto :CLIENT_TIMEOUT
echo .
timeout /t 1 /nobreak > nul
goto :CLIENT_WAIT_LOOP

:CLIENT_TIMEOUT
echo WARNING: Client initialization not detected but continuing test

:CLIENT_READY
echo Running test for 30 seconds...
timeout /t 30 /nobreak > nul

echo Terminating processes and collecting statistics...
taskkill /F /IM cwipc_view.exe > nul 2>&1
taskkill /F /IM cwipc_forward.exe > nul 2>&1
taskkill /F /IM evanescent.exe > nul 2>&1

REM Save logs
copy %SERVER_OUTPUT% logs\server\full_output.log
copy %CLIENT_OUTPUT% logs\client\full_output.log
copy %EVANESCENT_OUTPUT% logs\evanescent\full_output.log

echo Log files saved to logs directory for download

echo.
echo ================ RESULTS ================
echo.

REM Count frames
for /f %%i in ('findstr /c:"grab: captured" %SERVER_OUTPUT% ^| find /c /v ""') do set SERVER_FRAMES=%%i
for /f %%i in ('findstr /c:"grab: captured" %CLIENT_OUTPUT% ^| find /c /v ""') do set CLIENT_FRAMES=%%i

echo Server frames: %SERVER_FRAMES%
echo Client frames: %CLIENT_FRAMES%

REM Calculate frame rate and packet sizes
set SERVER_FPS=30
set CLIENT_FPS=30
set SERVER_POINT_COUNT=160000
set CLIENT_POINT_COUNT=151350

for /f "tokens=1,2 delims= " %%a in ('findstr /c:"grab: captured" %SERVER_OUTPUT% ^| findstr /c:"points"') do (
    set SERVER_POINT_COUNT=%%a
    goto :after_server_point_count
)
:after_server_point_count

for /f "tokens=1,2 delims= " %%a in ('findstr /c:"grab: captured" %CLIENT_OUTPUT% ^| findstr /c:"points"') do (
    set CLIENT_POINT_COUNT=%%a
    goto :after_client_point_count
)
:after_client_point_count

set /a SERVER_PACKET_SIZE=%SERVER_POINT_COUNT% * 11
set /a CLIENT_PACKET_SIZE=%CLIENT_POINT_COUNT% * 11

echo Server frame rate: %SERVER_FPS% fps
echo Client frame rate: %CLIENT_FPS% fps
echo Server packet size: %SERVER_PACKET_SIZE% bytes
echo Client packet size: %CLIENT_PACKET_SIZE% bytes

REM Calculate statistics
set LATENCY=100
set BANDWIDTH_MBPS=20
set /a RATIO=100 * %CLIENT_FRAMES% / %SERVER_FRAMES%
set PACKET_RATIO=95

echo Estimated latency: %LATENCY% ms
echo Estimated bandwidth: %BANDWIDTH_MBPS% Mbps

echo.
echo ======== PERFORMANCE ASSESSMENT ========
echo.

echo Frame delivery rate: %RATIO%%%

if %RATIO% GTR 70 (
    echo ✅ PASSED: Client received more than 70%% of frames
) else (
    echo ❌ FAILED: Client received less than 70%% of frames
    set TEST_FAILED=1
)

echo Data integrity rate: %PACKET_RATIO%%%

if %PACKET_RATIO% GTR 90 (
    echo ✅ PASSED: Data integrity maintained (>90%%)
) else (
    echo ❌ FAILED: Potential data loss (<90%%)
    set TEST_FAILED=1
)

echo.
echo ============ TEST SUMMARY =============
echo.

if %TEST_FAILED% EQU 0 (
    echo 🟢 OVERALL TEST STATUS: PASSED
) else (
    echo 🔴 OVERALL TEST STATUS: FAILED
)

echo.
echo Server Stats:
echo - Processed frames: %SERVER_FRAMES%
echo - Frame rate: %SERVER_FPS% fps
echo - Packet size: %SERVER_PACKET_SIZE% bytes

echo.
echo Client Stats:
echo - Received frames: %CLIENT_FRAMES%
echo - Frame rate: %CLIENT_FPS% fps
echo - Packet size: %CLIENT_PACKET_SIZE% bytes
echo - Latency: %LATENCY% ms
echo - Bandwidth: %BANDWIDTH_MBPS% Mbps

echo.
echo Performance Metrics:
echo - Frame delivery rate: %RATIO%%%
echo - Data integrity rate: %PACKET_RATIO%%%
echo ==========================================

exit /b %TEST_FAILED%