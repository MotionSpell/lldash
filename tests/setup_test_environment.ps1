# Setup a test environment.
# Use with "source", don't run normally.
# Installs cwipc, creates a venv in .venv, and installs the cwipc python modules.
# Adds ./installed/bin to PATH
curl.exe -L -o cwipc-built.zip https://github.com/cwi-dis/cwipc/releases/download/lldash-api-test-1/cwipc-win10-lldash-api-test-1-built.zip
Expand-Archive -path .\cwipc-built.zip -Force
$lldash_dir = Join-Path $PWD installed
$lldash_bin_dir = Join-Path $lldash_dir bin
$cwipc_dir = Join-Path $PWD cwipc-built\installed
$cwipc_bin_dir = Join-Path $cwipc_dir bin

$env:Path = $cwipc_bin_dir + ";" + $lldash_bin_dir + ";" + $env:Path

python -m venv .venv
& .\.venv\Scripts\Activate.ps1

cwipc_pymodules_install.ps1

$Env:SIGNALS_SMD_PATH=$lldash_bin_dir

if ($env:GITHUB_ACTIONS) {
    echo "SIGNALS_SMD_PATH=$Env:SIGNALS_SMD_PATH" | Out-File -FilePath $Env:GITHUB_ENV -Encoding utf8 -Append
    echo "$cwipc_bin_dir" | Out-File -FilePath $Env:GITHUB_PATH -Encoding utf8 -Append
    echo "$lldash_bin_dir" | Out-File -FilePath $Env:GITHUB_PATH -Encoding utf8 -Append
}