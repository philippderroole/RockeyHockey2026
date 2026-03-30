# Crosscompilation to Raspberry Pi OS (arm64) using system OpenCV
#
# Building this image requries `qemu-aarch64` to be present on the host system and the corresponding `binfmt-misc` set up (see
# e.g. https://wiki.debian.org/QemuUserEmulation, only `Installing packages` should be enough).
#
# After the successful build you will have an image configured for cross-compilation to Raspberry Pi. It will contain the
# sample build script `/usr/local/bin/cargo-xbuild` that you can check for the correct environment setup and the specific
# command line arguments to use when cross-compiling the project inside the container created from that image.


# Download and extract rpi root filesystem
FROM alpine:3.22

# OpenCV version comes from the selected Raspberry Pi OS rootfs.
# To match your Pi, change this image URL/date to a release with the same OpenCV package version.
ADD https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2024-11-19/2024-11-19-raspios-bookworm-arm64-lite.img.xz /raspios-lite-arm64.img.xz

# chmod calls are necessary because 7zip doesn't preserve file permissions during extraction
RUN set -xeu && \
    apk add xz 7zip && \
    unxz /raspios-lite-arm64.img.xz && \
    7z x -so /raspios-lite-arm64.img 1.img > rootfs.img && \
    7z x -snld -o/rpi-root rootfs.img && \
    chmod -R 755 /rpi-root/bin /rpi-root/boot /rpi-root/dev /rpi-root/etc /rpi-root/home /rpi-root/lib /rpi-root/media \
    /rpi-root/mnt /rpi-root/opt /rpi-root/run /rpi-root/sbin /rpi-root/srv /rpi-root/usr /rpi-root/var && \
    chmod -R 1777 /rpi-root/tmp && \
    chmod -R 555 /rpi-root/sys /rpi-root/proc && \
    chmod -R 700 /rpi-root/root

# Prepare the root of the rpi filesystem, it's going to be used later for cross-compilation
# This step requries qemu-arm to be present on the host system and the corresponding binfmt-misc set up
FROM scratch

COPY --from=0 /rpi-root /

# initramfs-tools breaking dist-upgrade in Docker:
# mkinitramfs: failed to determine device for /
RUN set -xeu && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y mawk && \
    ln -sf /usr/bin/mawk /usr/bin/awk && \
    DEBIAN_FRONTEND=noninteractive apt-get purge -y initramfs-tools cloud-init openssh-server ssh

RUN set -xeu && \
    ln -sf /usr/bin/mawk /usr/bin/awk && \
    apt-get autoremove -y --purge && \
    apt-get -y autoclean

RUN set -xeu && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y symlinks

# error: undefined symbol: _dl_pagesize (and __pointer_chk_guard_local)
# solution: fix broken absolute symlinks in the extracted rootfs to relative ones
# source: https://github.com/Azure/azure-iot-sdk-c/issues/1093
RUN set -xeu && \
    symlinks -cr /

# Specify dependencies that you need to have on rpi
RUN set -xeu && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y libopencv-dev


# Create the image that will be used for cross-compilation
FROM ubuntu:24.04

COPY --from=1 / /rpi-root

RUN set -xeu && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y && \
    apt-get autoremove -y --purge && \
    apt-get -y autoclean

RUN set -xeu && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y clang libclang-dev lld curl git build-essential cmake

RUN set -xeu && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile=minimal && \
    rm -rf /root/.rustup/tmp/* # warning: could not delete temp directory: /root/.rustup/tmp/szyc3h06vricp83o_dir

ENV PATH="${PATH}:/root/.cargo/bin"

RUN set -xeu && \
    rustup target add aarch64-unknown-linux-gnu

RUN set -xeu && \
    echo "[target.aarch64-unknown-linux-gnu]\nlinker = \"clang-rpi\"" > /root/.cargo/config.toml

RUN echo '#!/bin/bash\n\
    RPI_ROOT="/rpi-root"\n\
    GCC_INSTALL_DIR="$(find "$RPI_ROOT/usr/lib/gcc/aarch64-linux-gnu" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -n 1)"\n\
    clang --target=aarch64-linux-gnu -fuse-ld=lld --sysroot="$RPI_ROOT" --gcc-install-dir="$GCC_INSTALL_DIR" -Wl,-z,notext -Wno-unused-command-line-argument "$@"' > /usr/local/bin/clang-rpi && \
    chmod +x /usr/local/bin/clang-rpi

RUN echo '#!/bin/bash\n\
    RPI_ROOT="/rpi-root"\n\
    export OpenCV_DIR="$RPI_ROOT/usr/lib/aarch64-linux-gnu/cmake"\n\
    export CC_aarch64_unknown_linux_gnu=clang-rpi\n\
    export CXX_aarch64_unknown_linux_gnu=clang-rpi\n\
    export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER=clang-rpi\n\
    export BINDGEN_EXTRA_CLANG_ARGS_aarch64_unknown_linux_gnu="--sysroot=${RPI_ROOT}"\n\
    export CMAKE_CROSSCOMPILING=TRUE\n\
    cargo build -vv --target aarch64-unknown-linux-gnu' > /usr/local/bin/cargo-xbuild && chmod +x /usr/local/bin/cargo-xbuild