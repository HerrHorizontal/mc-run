#!/bin/sh

# source grid environment
source /cvmfs/grid.cern.ch/centos7-wn-4.0.5-1_umd4v1/etc/profile.d/setup-c7-wn-example.sh

# setup Herwig
export INSTALL_LOC=/cvmfs/etp.kit.edu/herwig/
export HERWIGPATH=/cvmfs/etp.kit.edu/herwig/
export PATH=$INSTALL_LOC/bin:$PATH
export LHAPDF=/cvmfs/etp.kit.edu/herwig/
export PATH=$PATH:$LHAPDF/bin
export LD_LIBRARY_PATH=$LHAPDF/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$LHAPDF/lib/python2.7/site-packages:$PYTHONPATH
# activate Herwig
source /cvmfs/etp.kit.edu/herwig/bin/activate

