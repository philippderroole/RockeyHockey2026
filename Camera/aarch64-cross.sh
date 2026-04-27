#!/usr/bin/env bash
set -euo pipefail

# PROJECT_DIR=/absolute/path/to/Camera ./build-release.sh
PROJECT_DIR="${PROJECT_DIR:-$PWD}"

IMAGE_NAME="rockeyhockey/camera-cross:latest"
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  echo "Image $IMAGE_NAME not found. Building it first..."
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR"
fi

CARGO_REGISTRY_MOUNT="${HOME}/.cargo/registry"
CARGO_GIT_MOUNT="${HOME}/.cargo/git"

mkdir -p "$CARGO_REGISTRY_MOUNT" "$CARGO_GIT_MOUNT"

echo "Building release binary for aarch64-unknown-linux-gnu"
docker run --rm \
  -v "$PROJECT_DIR:/work" \
  -v "$CARGO_REGISTRY_MOUNT:/root/.cargo/registry" \
  -v "$CARGO_GIT_MOUNT:/root/.cargo/git" \
  -w /work \
  "$IMAGE_NAME" \
  bash -lc '
    set -euo pipefail

    RPI_ROOT="/rpi-root"
    export OpenCV_DIR="${RPI_ROOT}/usr/lib/aarch64-linux-gnu/cmake/opencv4"
    export CMAKE_PREFIX_PATH="${OpenCV_DIR}:${RPI_ROOT}/usr/lib/aarch64-linux-gnu/cmake"
    export OPENCV_PKGCONFIG_NAME="opencv4"
    export PKG_CONFIG_SYSROOT_DIR="${RPI_ROOT}"
    export PKG_CONFIG_LIBDIR="${RPI_ROOT}/usr/lib/aarch64-linux-gnu/pkgconfig:${RPI_ROOT}/usr/share/pkgconfig"
    export PKG_CONFIG_PATH="${RPI_ROOT}/usr/lib/aarch64-linux-gnu/pkgconfig"
    export CC_aarch64_unknown_linux_gnu=clang-rpi
    export CXX_aarch64_unknown_linux_gnu=clang-rpi
    export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER=clang-rpi
    export BINDGEN_EXTRA_CLANG_ARGS_aarch64_unknown_linux_gnu="--sysroot=${RPI_ROOT}"
    export CMAKE_CROSSCOMPILING=TRUE
    
    cargo build -vv --release --target aarch64-unknown-linux-gnu
  '

echo "Done. Binary should be in: $PROJECT_DIR/target/aarch64-unknown-linux-gnu/release/"

# Remove image to force rebuild next time (ensures image matches your Pi's OpenCV version)
docker image rm "$IMAGE_NAME" || true
