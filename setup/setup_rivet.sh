#!/bin/sh

action(){
    # source grid environment
    source /cvmfs/grid.cern.ch/centos7-wn-4.0.5-1_umd4v1/etc/profile.d/setup-c7-wn-example.sh

    # Set up Rivet
    # Set up GCC and Python (v3 also supported):
    source /cvmfs/sft.cern.ch/lcg/releases/LCG_96/Python/2.7.16/x86_64-centos7-gcc62-opt/Python-env.sh
    # Set up Rivet
    source /cvmfs/sft.cern.ch/lcg/releases/LCG_96b/MCGenerators/rivet/3.1.2/x86_64-centos7-gcc8-opt/rivetenv-genser.sh
    # Set up a working LaTeX (needed if on lxplus7)
    export PATH=/cvmfs/sft.cern.ch/lcg/external/texlive/2016/bin/x86_64-linux:$PATH

    # Export rivet analysis path for plugin analyses
    if [ ! -z "$ZSH_VERSION" ]; then
        local this_file="${(%):-%x}"
    else
        local this_file="${BASH_SOURCE[0]}"
    fi
    local base="$( cd "$( dirname "$this_file" )" && pwd)"
    local parent="$( dirname "$base" )"

    export RIVET_ANALYSIS_PATH="$parent/analyses:$RIVET_ANALYSIS_PATH"
    #export RIVET_INFO_PATH="$RIVET_ANALYSIS_PATH"
}

action "$@"

    