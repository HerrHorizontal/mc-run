#!/bin/bash

source_sherpa() {
    # local variables
    local this_file
    local this_dir
    # shellcheck disable=SC2296
    this_file="$( [ -n "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
    this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

    source /cvmfs/cms.cern.ch/cmsset_default.sh
    pushd "$this_dir/../software/CMSSW_10_6_40/src" > /dev/null || exit
    eval "$(scramv1 runtime -sh)"
    popd > /dev/null || exit
    export PATH=$PATH:/cvmfs/cms.cern.ch/slc7_amd64_gcc700/external/sherpa/2.2.15-3ed6122ae1412ab3c132a3b5c3c9d9ff/bin
    Sherpa --version
}

source_sherpa "$@"
