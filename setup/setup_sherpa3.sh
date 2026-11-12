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

source_sherpa() {
    INSTALL_DIR="$this_dir/../software/sherpa3.0"
    if [[ ! -d "$INSTALL_DIR" ]]; then
        echo "Error: Sherpa installation directory $INSTALL_DIR does not exist. Installing..."
        source "$this_dir/install_sherpa3.sh"
    fi
    source_lcg_stack
    export SHERPA_INCLUDE_PATH=$INSTALL_DIR/include/SHERPA-MC
    export SHERPA_SHARE_PATH=$INSTALL_DIR/share/SHERPA-MC
    export SHERPA_LIBRARY_PATH=$INSTALL_DIR/lib64/SHERPA-MC
    export LD_LIBRARY_PATH=$SHERPA_LIBRARY_PATH:$LD_LIBRARY_PATH
    export PATH=$INSTALL_DIR/bin:$PATH
}

source_sherpa "$@"
Sherpa --version
