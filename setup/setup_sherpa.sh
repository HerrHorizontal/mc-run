#!/bin/bash

# determine the directy of this file
if [ -n "$ZSH_VERSION" ]; then
    this_file="${(%):-%x}"
else
    this_file="${BASH_SOURCE[0]}"
fi
this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

source_sherpa() {
    # Check OS and source Sherpa with dependencies from according LCG Stack
    base=/cvmfs/sft.cern.ch/lcg/releases
    LCG=LCG_105
    local prefix
    source "$this_dir/os-version.sh"
    if [[ "$distro" == "CentOS" ]]; then
        if [[ ${os_version:0:1} == "7" ]]; then
            prefix=x86_64-centos7
        fi
    elif [[ "$distro" == "RedHatEnterprise" || "$distro" == "Alma" || "$distro" == "Rocky" ]]; then
        if [[ ${os_version:0:1} == "9" ]]; then
            prefix=x86_64-el9
        fi
    elif [[ "$distro" == "Ubuntu" ]]; then
        if [[ ${os_version:0:2} == "22" ]]; then
            prefix=x86_64-ubuntu2204
        fi
    fi
    if [[ -z "$prefix" ]]; then
        echo "Sherpa with LCG Stack $LCG not available for $distro $os_version"
        return 1
    fi
    platform=${prefix}-gcc11-opt
    gccver=11.3.0-ad0f5

    export LD_LIBRARY_PATH=${base}/gcc/${gccver}/${prefix}/lib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/gcc/${gccver}/${prefix}/lib64:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/binutils/2.37-355ed/${prefix}/lib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/CppUnit/1.14.0/${platform}/lib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/Python/3.9.12/${platform}/lib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/sqlite/3320300/${platform}/lib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/fastjet/3.4.1/${platform}/lib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/MCGenerators/openloops/2.1.2/${platform}/lib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/MCGenerators/openloops/2.1.2/${platform}/proclib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/MCGenerators/lhapdf/6.5.3/${platform}/lib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/MCGenerators/sherpa/2.2.15/${platform}/lib/SHERPA-MC:$LD_LIBRARY_PATH
    if [[ "$distro" == "Ubuntu" ]]; then
        export LD_LIBRARY_PATH=${base}/${LCG}/hepmc3/3.2.7/${platform}/lib:$LD_LIBRARY_PATH
    else
        export LD_LIBRARY_PATH=${base}/${LCG}/hepmc3/3.2.7/${platform}/lib64:$LD_LIBRARY_PATH
    fi

    export PATH=${base}/gcc/${gccver}/${prefix}/bin:$PATH
    export PATH=${base}/binutils/2.37-355ed/${prefix}/bin:$PATH
    export PATH=${base}/${LCG}/numpy/1.23.5/${platform}/bin:$PATH
    export PATH=${base}/${LCG}/sqlite/3320300/${platform}/bin:$PATH
    export PATH=${base}/${LCG}/Python/3.9.12/${platform}/bin:$PATH
    export PATH=${base}/${LCG}/pip/22.0.4/${platform}/bin::$PATH
    export PATH=${base}/${LCG}/MCGenerators/sherpa/2.2.15/${platform}/bin:$PATH

    export LHAPDF_DATA_PATH=$LHAPDF_DATA_PATH:${base}/${LCG}/MCGenerators/lhapdf/6.5.3/${platform}/share/LHAPDF:/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current
}

source_sherpa "$@"
Sherpa --version
