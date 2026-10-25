#!/bin/sh
# Optional tool runtime, isolated from the dependency-free harness.
set -eu
tool_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
runtime_dir="$tool_root/.runtime"
python3 -m pip install --disable-pip-version-check --target "$runtime_dir/bootstrap" 'uv==0.13.5'
export UV_CACHE_DIR="$runtime_dir/cache"
export UV_PYTHON_INSTALL_DIR="$runtime_dir/python"
export UV_PROJECT_ENVIRONMENT="$runtime_dir/venv"
"$runtime_dir/bootstrap/bin/uv" sync --project "$tool_root/upstream" --python 3.12 --frozen --no-editable
