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
    local view_base=/cvmfs/sft.cern.ch/lcg/views
    LCG=LCG_105
    local prefix
    local grid_ui
    source $this_dir/setup/os-version.sh
    if [[ "$distro" == "CentOS" ]]; then
        if [[ ${os_version:0:1} == "7" ]]; then
            prefix=x86_64-centos7
            grid_ui="/cvmfs/grid.cern.ch/centos7-ui-200122/etc/profile.d/setup-c7-ui-python3-example.sh"
        fi
    elif [[ "$distro" == "RedHatEnterprise" || "$distro" == "Alma" || "$distro" == "Rocky" ]]; then
        if [[ ${os_version:0:1} == "9" ]]; then
            prefix=x86_64-el9
            grid_ui="/cvmfs/grid.cern.ch/alma9-ui-test/etc/profile.d/setup-alma9-test.sh"
        fi
    elif [[ "$distro" == "Ubuntu" ]]; then
        if [[ ${os_version:0:2} == "22" ]]; then
            prefix=x86_64-ubuntu2204
        fi
    fi
    if [[ -z "$prefix" ]]; then
        echo "LCG Stack $LCG not available for $distro $os_version"
        return 1
    fi
    platform=${prefix}-gcc11-opt
    local lcg_path=$view_base/$LCG/$platform/setup.sh
    echo "Sourcing LCG Stack from $lcg_path"
    # shellcheck disable=SC1090
    source "$lcg_path"
    echo "Sourcing grid-ui from $grid_ui"
    # shellcheck disable=SC1090
    source "$grid_ui"
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
