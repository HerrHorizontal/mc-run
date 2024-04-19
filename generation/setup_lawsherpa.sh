#!/bin/bash

action(){
    # source grid environment
    source /cvmfs/grid.cern.ch/centos7-wn-4.0.5-1_umd4v1/etc/profile.d/setup-c7-wn-example.sh

    # untar tarball
    echo "Untarring tarball"
    tar -xzf generation*.tar.gz
    rm generation*.tar.gz

    # setup law
    echo "Setting up law"
    export LAW_HOME="$PWD/.law"
    export LAW_CONFIG_FILE="$PWD/law.cfg"
    export LUIGI_CONFIG_PATH="$PWD/luigi.cfg"

    export ANALYSIS_PATH="$PWD"
    export ANALYSIS_DATA_PATH="$ANALYSIS_PATH"

    export PATH="$PWD/law/bin:$PWD/luigi/bin:$PATH"
    export PYTHONPATH="$PWD/enum34-1.1.10:$PWD/law:$PWD/luigi:$PWD/six:$PWD:$PYTHONPATH"

    # setup Sherpa
    CMSSW_VERSION="CMSSW_10_6_40"
    CMSSW_DIR="software/$CMSSW_VERSION"
    echo "Setting up Sherpa with CMSSW at $CMSSW_DIR"
    source /cvmfs/cms.cern.ch/cmsset_default.sh
    scram project -n "$CMSSW_DIR" CMSSW "$CMSSW_VERSION"
    # extract custom cmssw modules/code here, if any
    pushd "$CMSSW_DIR/src" > /dev/null || exit
    eval "$(scramv1 runtime -sh)"
    popd > /dev/null || exit
    echo "CMSSW environment set up. Loading Sherpa..."
    export PATH=$PATH:/cvmfs/cms.cern.ch/slc7_amd64_gcc700/external/sherpa/2.2.15-3ed6122ae1412ab3c132a3b5c3c9d9ff/bin
    # TMPDIR overwrite needed for Sherpa because of MPI?
    export TMPDIR="/tmp"
    Sherpa --version
}

action "$@"
