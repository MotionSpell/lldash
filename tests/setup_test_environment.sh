# Setup a test environment.
# Use with "source", don't run normally.
# Installs cwipc, creates a venv in .venv, and installs the cwipc python modules.
# Adds ./installed/bin to PATH
cwipc_version_tag=v8.0.0
if [ $(uname) = "Linux" ]; then
    sudo apt install -y python3.12-venv
    
    curl -L -o cwipc-built.tar.gz https://github.com/cwi-dis/cwipc/releases/download/${cwipc_version_tag}/cwipc-ubuntu2404-amd64-built-${cwipc_version_tag}.tar.gz
    (cd installed && tar xfv ../cwipc-built.tar.gz)
    
    bash installed/libexec/cwipc/scripts/install-3rdparty-ubuntu2404.sh
    
elif [ $(uname) = "Darwin" -a $(arch) = "arm64" ]; then
    mkdir -p installed
    curl -L -o cwipc-built.tar.gz https://github.com/cwi-dis/cwipc/releases/download/${cwipc_version_tag}/cwipc-macos-arm64-built-${cwipc_version_tag}.tar.gz
    (cd installed && tar xfv ../cwipc-built.tar.gz)
    bash installed/libexec/cwipc/scripts/install-3rdparty-macos.sh
elif [ $(uname) = "Darwin" ]; then
    mkdir -p installed
    curl -L -o cwipc-built.tar.gz https://github.com/cwi-dis/cwipc/releases/download/${cwipc_version_tag}/cwipc-macos-intel-built-${cwipc_version_tag}.tar.gz
    (cd installed && tar xfv ../cwipc-built.tar.gz)
    bash installed/libexec/cwipc/scripts/install-3rdparty-macos.sh
elif false; then
    brew tap cwi-dis/cwipc
    # Workaround for git-lfs issue with brew install --head:
    GIT_LFS_WTD="$(git --exec-path)/git-lfs"
    if [ ! -f ${GIT_LFS_WTD} ]; then
        ln -s "$(which git-lfs)" ${GIT_LFS_WTD}
    fi
    # Workaround for issue cwipc#192
    brew install libomp
    brew link --force libomp
    HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1 brew install --head cwipc
else
    echo "Unsupported OS"
fi

export PATH=$(pwd)/installed/bin:$PATH
export LD_LIBRARY_PATH=$(pwd)/installed/lib:$LD_LIBRARY_PATH
export DYLD_LIBRARY_PATH=$(pwd)/installed/lib:$DYLD_LIBRARY_PATH
export SIGNALS_SMD_PATH=$(pwd)/installed/lib/

python3.12 -m venv .venv
source .venv/bin/activate
CWIPC_PYTHON=$(which python) cwipc_pymodules_install.sh || true

if [ "${GITHUB_ACTIONS:-false}" = true ]; then
    # GitHub actions
    echo $(pwd)/installed/bin >> $GITHUB_PATH
    echo "LD_LIBRARY_PATH=$(pwd)/installed/lib:$LD_LIBRARY_PATH" >> $GITHUB_ENV
    echo "DYLD_LIBRARY_PATH=$(pwd)/installed/lib:$DYLD_LIBRARY_PATH" >> $GITHUB_ENV
    echo "SIGNALS_SMD_PATH=$(pwd)/installed/lib/" >> $GITHUB_ENV
fi
