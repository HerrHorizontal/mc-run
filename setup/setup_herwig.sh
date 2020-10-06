#!/bin/sh

# source grid environment
source /cvmfs/grid.cern.ch/centos7-wn-4.0.5-1_umd4v1/etc/profile.d/setup-c7-wn-example.sh

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

