#!/bin/bash
#################################################################
# This script setups all dependencies necessary for running law #
#################################################################

# determine the directy of this file
if [ -n "$ZSH_VERSION" ]; then
    this_file="${(%):-%x}"
else
    this_file="${BASH_SOURCE[0]}"
fi
this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

source_lcg_stack() {
    # Check OS and source according LCG Stack
    local lcg_base="/cvmfs/sft.cern.ch/lcg/views/LCG_105"
    local lcg_path
    source "$this_dir/setup/os-version.sh"
    if [[ "$distro" == "CentOS" ]]; then
        if [[ ${os_version:0:1} == "7" ]]; then
            lcg_path="$lcg_base/x86_64-centos7-gcc11-opt/setup.sh"
        fi
    elif [[ "$distro" == "RedHatEnterprise" || "$distro" == "Alma" || "$distro" == "Rocky" ]]; then
        if [[ ${os_version:0:1} == "9" ]]; then
            lcg_path="$lcg_base/x86_64-el9-gcc11-opt/setup.sh"
        fi
    elif [[ "$distro" == "Ubuntu" ]]; then
        if [[ ${os_version:0:2} == "20" ]]; then
            lcg_path="$lcg_base/x86_64-ubuntu2004-gcc9-opt/setup.sh"
        elif [[ ${os_version:0:2} == "22" ]]; then
            lcg_path="$lcg_base/x86_64-ubuntu2204-gcc11-opt/setup.sh"
        fi
    fi
    if [[ -z "$lcg_path" ]]; then
        echo "LCG Stack $lcg_base not available for $distro $os_version"
        return 1
    fi
    echo "Sourcing LCG Stack from $lcg_path"
    # shellcheck disable=SC1090
    source "$lcg_path"
}

action() {
    # source lcg stack
    source_lcg_stack
    _addpy() {
        [ -n "$1" ] && export PYTHONPATH="$1:$PYTHONPATH"
    }
    _addbin() {
        [ -n "$1" ] && export PATH="$1:$PATH"
    }

    export LAW_HOME="$this_dir/.law"
    export LAW_CONFIG_FILE="$this_dir/law.cfg"
    export LUIGI_CONFIG_PATH="$this_dir/luigi.cfg"
    export ANALYSIS_PATH="$this_dir"
    export ANALYSIS_DATA_PATH="$this_dir/data"

    # luigi
    _addpy "$this_dir/luigi"
    _addbin "$this_dir/luigi/bin"

    # six
    _addpy "$this_dir/six"

    # scinum
    _addpy "$this_dir/scinum"

    # order
    _addpy "$this_dir/order"

    # law
    _addpy "$this_dir/law"
    _addbin "$this_dir/law/bin"

    # this analysis
    _addpy "$ANALYSIS_PATH"
    source "$( law completion )"
}

action "$@"
