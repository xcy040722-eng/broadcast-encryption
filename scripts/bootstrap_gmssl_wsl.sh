#!/usr/bin/env bash
set -euo pipefail

# Reproducible WSL/Ubuntu bootstrap for the SM2+SM4 backend + PySide6 workbench.
# Tested profile reported by the project:
#   Ubuntu 24.04 / Python 3.12
#   GmSSL native commit 24ae4827
#   gmssl-python 2.2.2 + project ABI patch
#   WSLg + PySide6 6.x
#
# UI note:
# - fonts-noto-cjk is installed so the default zh_CN interface does not render tofu boxes.
# - common Qt/xcb runtime libraries are installed for PySide6 under WSLg.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GMSSL_COMMIT="24ae4827"
GMSSL_SRC="${GMSSL_SRC:-/tmp/GmSSL-sm2-sm4}"
VENV="${VENV:-$ROOT_DIR/.venv-sm2-sm4}"

printf '[1/8] Installing build + WSLg UI prerequisites\n'
sudo apt-get update
sudo apt-get install -y \
  build-essential \
  cmake \
  git \
  python3-venv \
  python3-dev \
  fonts-noto-cjk \
  libxcb-cursor0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-randr0 \
  libxcb-render-util0 \
  libxcb-shape0 \
  libxcb-xinerama0 \
  libxcb-xkb1 \
  libxkbcommon-x11-0

printf '[2/8] Fetching pinned native GmSSL commit %s\n' "$GMSSL_COMMIT"
if [[ ! -d "$GMSSL_SRC/.git" ]]; then
  git clone https://github.com/guanzhi/GmSSL.git "$GMSSL_SRC"
fi
git -C "$GMSSL_SRC" fetch --all --tags --prune
git -C "$GMSSL_SRC" checkout --detach "$GMSSL_COMMIT"

printf '[3/8] Building native GmSSL\n'
rm -rf "$GMSSL_SRC/build"
cmake -S "$GMSSL_SRC" -B "$GMSSL_SRC/build"
cmake --build "$GMSSL_SRC/build" -j"$(nproc)"
ctest --test-dir "$GMSSL_SRC/build" --output-on-failure
sudo cmake --install "$GMSSL_SRC/build"
sudo ldconfig

printf '[4/8] Creating Python virtual environment: %s\n' "$VENV"
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip

printf '[5/8] Installing pinned Python dependencies\n'
python -m pip install -r "$ROOT_DIR/requirements-sm2-sm4.txt"

printf '[6/8] Applying verified ctypes ABI compatibility patch\n'
python "$ROOT_DIR/tools/patch_gmssl_python_abi.py"
python "$ROOT_DIR/tools/patch_gmssl_python_abi.py" --check

printf '[7/8] Running real integration test\n'
cd "$ROOT_DIR"
pytest -q -rs tests/test_sm2_sm4_mre_gmssl_integration.py

printf '[8/8] Running all SM2/SM4 backend tests\n'
pytest -q -rs tests/test_sm2_sm4_mre_*.py

printf '\nBootstrap completed successfully.\n'
printf 'Activate later with: source %q/bin/activate\n' "$VENV"
