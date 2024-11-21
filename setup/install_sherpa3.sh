#!/bin/bash

# determine the directy of this file
if [ -n "$ZSH_VERSION" ]; then
    this_file="${(%):-%x}"
else
    this_file="${BASH_SOURCE[0]}"
fi
this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

source_lcg_stack() {
    # Check OS and source Sherpa with dependencies from according LCG Stack
    base=/cvmfs/sft.cern.ch/lcg/releases
    view_base=/cvmfs/sft.cern.ch/lcg/views
    LCG=LCG_106
    local prefix
    source "$this_dir/os-version.sh"
    if [[ "$distro" == "RedHatEnterprise" || "$distro" == "Alma" || "$distro" == "Rocky" ]]; then
        if [[ ${os_version:0:1} == "9" ]]; then
            prefix=x86_64-el9
        fi
    fi
    if [[ -z "$prefix" ]]; then
        echo "Sherpa3 with LCG Stack $LCG not set up and/or tested for $distro $os_version"
        return 1
    fi
    platform=${prefix}-gcc13-opt
    local lcg_path=$view_base/$LCG/$platform/setup.sh
    echo "Sourcing LCG Stack from $lcg_path"
    # shellcheck disable=SC1090
    source "$lcg_path"

    # set OpenLoops prefix
    export OL_PREFIX=$base/$LCG/MCGenerators/openloops/2.1.2/$platform
}

install_sherpa() {
    source_lcg_stack
    INSTALL_DIR="$this_dir/../software/sherpa3.0"
    mkdir -p "$INSTALL_DIR"
    BUILD_DIR="$this_dir/../src/"
    mkdir -p "$BUILD_DIR"

    if [ ! -d "$BUILD_DIR/sherpa" ]; then
        git clone -b "rel-3-0-x" https://gitlab.com/sherpa-team/sherpa.git "$BUILD_DIR/sherpa"
    fi
    cmake --fresh -S "$BUILD_DIR/sherpa" -B "$BUILD_DIR/sherpa" \
        -DSHERPA_ENABLE_INSTALL_LIBZIP=ON \
        -DSHERPA_ENABLE_MPI=ON \
        -DSHERPA_ENABLE_HEPMC3=ON \
        -DSHERPA_ENABLE_RIVET=ON \
        -DOPENLOOPS_PREFIX="$OL_PREFIX" \
        -DSHERPA_ENABLE_OPENLOOPS=ON
    cmake --build "$BUILD_DIR/sherpa" -j 8
    cmake --install "$BUILD_DIR/sherpa" --prefix "$INSTALL_DIR"
}

install_sherpa "$@"
