#!/bin/sh

action(){
    SPAWNPOINT=$(pwd)

    # source grid environment
    source /cvmfs/grid.cern.ch/centos7-wn-4.0.5-1_umd4v1/etc/profile.d/setup-c7-wn-example.sh


    # Set up Rivet
    source /cvmfs/sft.cern.ch/lcg/releases/LCG_96b/MCGenerators/rivet/3.1.2/x86_64-centos7-gcc8-opt/rivetenv-genser.sh
    # Set up a working LaTeX (needed if on lxplus7)
    export PATH=/cvmfs/sft.cern.ch/lcg/external/texlive/2016/bin/x86_64-linux:$PATH

    
    # Set up GCC and Python (v3 also supported):
    source /cvmfs/sft.cern.ch/lcg/releases/LCG_96/Python/2.7.16/x86_64-centos7-gcc62-opt/Python-env.sh

    # untar tarball
    tar -xzf generation*.tar.gz
    rm generation*.tar.gz

    # Set up law
    export LAW_HOME="$PWD/.law"
    export LAW_CONFIG_FILE="$PWD/law.cfg"
    export LUIGI_CONFIG_PATH="$PWD/luigi.cfg"

    export ANALYSIS_PATH="$PWD"
    export ANALYSIS_DATA_PATH="$ANALYSIS_PATH"

    export PATH="$PWD/law/bin:$PWD/luigi/bin:$PATH"
    export PYTHONPATH="$PWD/enum34-1.1.10:$PWD/law:$PWD/luigi:$PWD/six:$PWD:$PYTHONPATH"


    # Export rivet analysis path for plugin analyses
    export RIVET_ANALYSIS_PATH="$ANALYSIS_PATH/analyses:$RIVET_ANALYSIS_PATH"

}

action
