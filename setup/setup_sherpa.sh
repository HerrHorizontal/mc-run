#!/bin/bash

source_sherpa() {
    # local variables
    local this_file
    local this_dir
    # shellcheck disable=SC2296
    this_file="$( [ -n "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
    this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

    source "$this_dir/os-version.sh"
    source /cvmfs/cms.cern.ch/cmsset_default.sh

    if [[ "$distro" == "CentOS" ]]; then
        if [[ ${os_version:0:1} == "7" ]]; then
            CMSSW_VERSION="CMSSW_12_4_20"
        fi
    elif [[ "$distro" == "RedHatEnterprise" || "$distro" == "Alma" || "$distro" == "Rocky" ]]; then
        if [[ ${os_version:0:1} == "8" || ${os_version:0:1} == "9" ]]; then
            CMSSW_VERSION="CMSSW_13_3_3"
        fi
    fi
    if [[ -z "$CMSSW_VERSION" ]]; then
        echo "CMSSW including Sherpa not available for $distro $os_version"
        return 1
    fi
    CMSSW_DIR="$this_dir/../software/$CMSSW_VERSION"
    if [[ ! -d $CMSSW_DIR ]]; then
        echo "Setting up Sherpa with CMSSW at $CMSSW_DIR"
        scram project -d "$CMSSW_DIR/../" CMSSW "$CMSSW_VERSION"
    fi
    pushd "$CMSSW_DIR/src" > /dev/null || exit
    echo "Loading Sherpa with $CMSSW_VERSION"
    eval "$(scramv1 runtime -sh)"
    sherpa_path="$(scram tool info Sherpa | grep BINDIR | cut -d "=" -f2)"
    export PATH="$PATH:$sherpa_path"
    popd > /dev/null || exit
    Sherpa --version
}

source_sherpa "$@"
