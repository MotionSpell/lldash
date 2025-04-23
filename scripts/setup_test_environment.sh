# Setup a test environment.
# Use with "source", don't run normally.
# Installs cwipc, creates a venv in .venv, and installs the cwipc python modules.
# Adds ./installed/bin to PATH

if [ $(uname) = "Linux" ]; then
    echo "Not implemented yet"
    exit 1
elif [ $(uname) = "Darwin" ]; then
    brew tap cwi-dis/cwipc
    # Workaround for issue cwipc#192
    HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1 brew install cwipc
    python3.12 -m venv .venv
    source .venv/bin/activate
    CWIPC_PYTHON=$(which python) cwipc_pymodules_install.sh || true
    export PATH=$(pwd)/installed/bin:$PATH
    export DYLD_LIBRARY_PATH=$(pwd)/installed/lib:$DYLD_LIBRARY_PATH
    export SIGNALS_SMD_PATH=$(pwd)/installed/lib/
else
    echo "Unsupported OS"
fi