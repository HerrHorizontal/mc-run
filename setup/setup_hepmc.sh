#!/bin/bash

# determine the directy of this file
if [ -n "$ZSH_VERSION" ]; then
    this_file="${(%):-%x}"
else
    this_file="${BASH_SOURCE[0]}"
fi
this_dir="$( cd "$( dirname "$this_file" )" && pwd )"


source_hepmc(){
    # Check OS and source HepMC3 (with ROOT I/O) and ROOT from according LCG Stack
    view_base=/cvmfs/sft.cern.ch/lcg/views
    LCG=LCG_110a
    local prefix
    local platform
    source "$this_dir/os-version.sh"
    if [[ "$distro" == "CentOS" ]]; then
        if [[ ${os_version:0:1} == "7" ]]; then
            echo "CentOS7 is not supported anymore! Use an updated OS."
            return 1
        fi
    elif [[ "$distro" == "RedHatEnterprise" || "$distro" == "Alma" || "$distro" == "Rocky" ]]; then
        if [[ ${os_version:0:1} == "9" ]]; then
            prefix=x86_64-el9
            platform=${prefix}-gcc15-opt
        fi
    elif [[ "$distro" == "Ubuntu" ]]; then
        if [[ ${os_version:0:2} == "22" ]]; then
            prefix=x86_64-ubuntu2204
            platform=${prefix}-gcc11-opt
        fi
    fi
    if [[ -z "$prefix" ]]; then
        echo "HepMC3 with LCG Stack $LCG not available for $distro $os_version"
        return 1
    fi
    local lcg_path=$view_base/$LCG/$platform/setup.sh
    echo "Sourcing LCG Stack from $lcg_path"
    # shellcheck disable=SC1090
    source "$lcg_path"
    # LCG release and platform, which determine the binary compatibility of compiled code
    export HEPMC_LCG_PLATFORM="$LCG/$platform"
}

source_hepmc "$@"
HepMC3-config --version
