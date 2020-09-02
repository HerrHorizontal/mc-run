#!/bin/sh

cd /local/scratch/ssd/mhorzela


export INSTALL_LOC=/cvmfs/pheno.egi.eu/Herwig/Herwig-7-2
export HERWIGPATH=/cvmfs/pheno.egi.eu/Herwig/Herwig-7-2
export PATH=$INSTALL_LOC/bin:$PATH
export LHAPDF=/cvmfs/pheno.egi.eu/Herwig
export PATH=$PATH:$LHAPDF/bin
export LD_LIBRARY_PATH=$LHAPDF/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$LHAPDF/lib/python2.7/site-packages:$PYTHONPATH

source /cvmfs/pheno.egi.eu/Herwig/bin/activate

Herwig read inputfiles/LHC-ZJetMerging.in
Herwig run LHC-Z-Merging.run -N 1000 -s 12345
