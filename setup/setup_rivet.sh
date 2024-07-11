#!/bin/bash

# determine the directy of this file
if [ -n "$ZSH_VERSION" ]; then
    this_file="${(%):-%x}"
else
    this_file="${BASH_SOURCE[0]}"
fi
this_dir="$( cd "$( dirname "$this_file" )" && pwd )"


source_rivet(){
    # Check OS and source Rivet with dependencies from according LCG Stack
    view_base=/cvmfs/sft.cern.ch/lcg/views
    LCG=LCG_105
    local prefix
    local platform
    source "$this_dir/os-version.sh"
    if [[ "$distro" == "CentOS" ]]; then
        if [[ ${os_version:0:1} == "7" ]]; then
            echo "CentOS7 is not supported anymore! Use an updated OS."
            return 1
            prefix=x86_64-centos7
            platform=${prefix}-gcc11-opt
        fi
    elif [[ "$distro" == "RedHatEnterprise" || "$distro" == "Alma" || "$distro" == "Rocky" ]]; then
        if [[ ${os_version:0:1} == "9" ]]; then
            prefix=x86_64-el9
            platform=${prefix}-gcc13-opt
        fi
    elif [[ "$distro" == "Ubuntu" ]]; then
        if [[ ${os_version:0:2} == "22" ]]; then
            prefix=x86_64-ubuntu2204
            platform=${prefix}-gcc11-opt
        fi
    fi
    if [[ -z "$prefix" ]]; then
        echo "Rivet with LCG Stack $LCG not available for $distro $os_version"
        return 1
    fi
    local lcg_path=$view_base/$LCG/$platform/setup.sh
    echo "Sourcing LCG Stack from $lcg_path"
    # shellcheck disable=SC1090
    source "$lcg_path"

    # Add local Rivet analyses to RIVET_ANALYSIS_PATH
    parent="$( dirname "$this_dir" )"
    echo "Adding Rivet analyses from $parent/analyses to RIVET_ANALYSIS_PATH"
    export RIVET_ANALYSIS_PATH="$parent/analyses:$RIVET_ANALYSIS_PATH"
    export RIVET_OS_DISTRO="$distro${os_version:0:1}"
}

source_rivet "$@"
rivet --version
