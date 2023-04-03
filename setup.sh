#!/usr/bin/env bash

############################################################################################
# This script setups all dependencies necessary for making law executable                  #
############################################################################################

action() {
    # determine the directy of this file
    if [ ! -z "$ZSH_VERSION" ]; then
        local this_file="${(%):-%x}"
    else
        local this_file="${BASH_SOURCE[0]}"
    fi
    #source /cvmfs/cms.cern.ch/slc6_amd64_gcc480/external/python/2.7.3/etc/profile.d/init.sh

    local base="$( cd "$( dirname "$this_file" )" && pwd )"
    local parent="$( dirname "$base" )"

    _addpy() {
        [ ! -z "$1" ] && export PYTHONPATH="$1:$PYTHONPATH"
    }

    _addbin() {
        [ ! -z "$1" ] && export PATH="$1:$PATH"
    }


    export LAW_HOME="$base/.law"
    export LAW_CONFIG_FILE="$base/law.cfg"
    export LUIGI_CONFIG_PATH="$base/luigi.cfg"
    export ANALYSIS_PATH="$base"
    export ANALYSIS_DATA_PATH="$ANALYSIS_PATH/data"



    # luigi
    _addpy "$base/luigi"
    _addbin "$base/luigi/bin"

    # enum34
    _addpy "$base/enum34-1.1.10"

    # six
    _addpy "$base/six"

    # scinum
    _addpy "$base/scinum"

    # order
    _addpy "$base/order"

    # law
    _addpy "$base/law"
    _addbin "$base/law/bin"
    source "$( law completion )"
    #source /cvmfs/grid.cern.ch/emi3ui-latest/etc/profile.d/setup-ui-example.sh
    source /cvmfs/grid.cern.ch/centos7-ui-4.0.3-1_umd4v1/etc/profile.d/setup-c7-ui-example.sh
}
action "$@"
