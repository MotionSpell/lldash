# Setup a test environment.
# Use with "source", don't run normally.
# Installs cwipc, creates a venv in .venv, and installs the cwipc python modules.
# Adds ./installed/bin to PATH

if [ $(uname) = "Linux" ]; then
    sudo apt install -y python3.12-venv
    
    curl -L -o cwipc-built.tar.gz https://github.com/cwi-dis/cwipc/releases/download/nightly/cwipc-ubuntu2404-nightly-built.tar.gz
    (cd installed && tar xfv ../cwipc-built.tar.gz)
    
    export PATH=$(pwd)/installed/bin:$PATH
    export LD_LIBRARY_PATH=$(pwd)/installed/lib:$LD_LIBRARY_PATH
    export SIGNALS_SMD_PATH=$(pwd)/installed/lib/
    
    bash installed/libexec/cwipc/scripts/install-3rdparty-ubuntu2404.sh

    python3.12 -m venv .venv
    source .venv/bin/activate
    CWIPC_PYTHON=$(which python) cwipc_pymodules_install.sh || true
    
    if [ "${GITHUB_ACTIONS:-false}" = true ]; then
        echo "$(pwd)/installed/bin" >> $GITHUB_PATH
        echo "LD_LIBRARY_PATH=$(pwd)/installed/lib:$LD_LIBRARY_PATH" >> $GITHUB_ENV
        echo "SIGNALS_SMD_PATH=$(pwd)/installed/lib/" >> $GITHUB_ENV
    fi

elif [ $(uname) = "Darwin" ]; then
    brew tap cwi-dis/cwipc
    # Workaround for issue cwipc#192
    HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1 brew install --head cwipc
    python3.12 -m venv .venv
    source .venv/bin/activate
    CWIPC_PYTHON=$(which python) cwipc_pymodules_install.sh || true
    export PATH=$(pwd)/installed/bin:$PATH
    export DYLD_LIBRARY_PATH=$(pwd)/installed/lib:$DYLD_LIBRARY_PATH
    export SIGNALS_SMD_PATH=$(pwd)/installed/lib/
    if [ "${GITHUB_ACTIONS:-false}" = true ]; then
        echo "$(pwd)/installed/bin" >> $GITHUB_PATH
        echo "DYLD_LIBRARY_PATH=$(pwd)/installed/lib:$DYLD_LIBRARY_PATH" >> $GITHUB_ENV
        echo "SIGNALS_SMD_PATH=$(pwd)/installed/lib/" >> $GITHUB_ENV
    fi
else
    echo "Unsupported OS"
fi

if [ "${GITHUB_ACTIONS:-false}" = true ]; then
    # GitHub actions
    echo $(pwd)/installed/bin >> $GITHUB_PATH
    echo "DYLD_LIBRARY_PATH=$(pwd)/installed/lib" >> $GITHUB_ENV
    export PATH=$(pwd)/installed/bin:$PATH
    export LD_LIBRARY_PATH=$(pwd)/installed/lib:$LD_LIBRARY_PATH
    export SIGNALS_SMD_PATH=$(pwd)/installed/lib/
fi