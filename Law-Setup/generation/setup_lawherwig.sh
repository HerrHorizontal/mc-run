#!/bin/sh

action(){
    SPAWNPOINT=$(pwd)

    # source grid environment
    source /cvmfs/grid.cern.ch/centos7-wn-4.0.5-1_umd4v1/etc/profile.d/setup-c7-wn-example.sh

    # untar tarball
    tar -xzf generation*.tar.gz
    rm generation*.tar.gz

    # setup law
    export LAW_HOME="$PWD/.law"
    export LAW_CONFIG_FILE="$PWD/law.cfg"
    export LUIGI_CONFIG_PATH="$PWD/luigi.cfg"

    export ANALYSIS_PATH="$PWD"
    export ANALYSIS_DATA_PATH="$ANALYSIS_PATH"

    export PATH="$PWD/law/bin:$PWD/luigi/bin:$PATH"
    export PYTHONPATH="$PWD/enum34-1.1.10:$PWD/law:$PWD/luigi:$PWD/six:$PWD:$PYTHONPATH"

    # setup Herwig
    export INSTALL_LOC=/cvmfs/pheno.egi.eu/Herwig/Herwig-7-2
    export HERWIGPATH=/cvmfs/pheno.egi.eu/Herwig/Herwig-7-2
    export PATH=$INSTALL_LOC/bin:$PATH
    export LHAPDF=/cvmfs/pheno.egi.eu/Herwig
    export PATH=$PATH:$LHAPDF/bin
    export LD_LIBRARY_PATH=$LHAPDF/lib:$LD_LIBRARY_PATH
    export PYTHONPATH=$LHAPDF/lib/python2.7/site-packages:$PYTHONPATH
    # activate Herwig
    source /cvmfs/pheno.egi.eu/Herwig/bin/activate

}

action
