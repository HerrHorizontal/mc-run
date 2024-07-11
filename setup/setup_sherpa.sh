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
    view_base=/cvmfs/sft.cern.ch/lcg/views
    LCG=LCG_105
    local prefix
    local platform
    source "$this_dir/os-version.sh"
    if [[ "$distro" == "CentOS" ]]; then
        if [[ ${os_version:0:1} == "7" ]]; then
            echo "CentOS7 is not supported anymore! Use an updated OS."
            return 1
            prefix=x86_64-centos7
            platform=${prefix}-gcc11-opt
        fi
    elif [[ "$distro" == "RedHatEnterprise" || "$distro" == "Alma" || "$distro" == "Rocky" ]]; then
        if [[ ${os_version:0:1} == "9" ]]; then
            prefix=x86_64-el9
            platform=${prefix}-gcc13-opt
        fi
    elif [[ "$distro" == "Ubuntu" ]]; then
        if [[ ${os_version:0:2} == "22" ]]; then
            prefix=x86_64-ubuntu2204
            platform=${prefix}-gcc11-opt
        fi
    fi
    if [[ -z "$prefix" ]]; then
        echo "Sherpa with LCG Stack $LCG not available for $distro $os_version"
        return 1
    fi
    local lcg_path=$view_base/$LCG/$platform/setup.sh
    echo "Sourcing LCG Stack from $lcg_path"
    # shellcheck disable=SC1090
    source "$lcg_path"
    # source openmpi for Sherpa multicore support, when compiling loop libs
    source $base/$LCG/openmpi/4.1.6/$platform/openmpi-env.sh
    # Export ACLOCAL_PATH, so sherpa makelibs will run (and other tools that use aclocal)
    export ACLOCAL_PATH=$view_base/$LCG/$platform/share/aclocal/:$ACLOCAL_PATH

    # Add MC Generators to LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/fastjet/3.4.1/${platform}/lib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/MCGenerators/openloops/2.1.2/${platform}/lib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/MCGenerators/openloops/2.1.2/${platform}/proclib:$LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/MCGenerators/lhapdf/6.5.3/${platform}/lib:$LD_LIBRARY_PATH
    # For some reason hepmc3 has separate lib and lib64 directories depending on the OS
    if [[ "$distro" == "Ubuntu" ]]; then
        export LD_LIBRARY_PATH=${base}/${LCG}/hepmc3/3.2.7/${platform}/lib:$LD_LIBRARY_PATH
    else
        export LD_LIBRARY_PATH=${base}/${LCG}/hepmc3/3.2.7/${platform}/lib64:$LD_LIBRARY_PATH
    fi
    # Add Sherpa with mpirun capabilities to LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${base}/${LCG}/MCGenerators/sherpa/2.2.15.openmpi3/${platform}/lib/SHERPA-MC:$LD_LIBRARY_PATH

    # Add Sherpa with mpirun capabilities to PATH
    export PATH=${base}/${LCG}/MCGenerators/sherpa/2.2.15.openmpi3/${platform}/bin:$PATH
    export CPLUS_INCLUDE_PATH=${base}/${LCG}/MCGenerators/sherpa/2.2.15.openmpi3/${platform}/include/SHERPA-MC:$CPLUS_INCLUDE_PATH
    # Specify LHAPDF path and the OpenLoops prefix
    export LHAPDF_DATA_PATH=$LHAPDF_DATA_PATH:${base}/${LCG}/MCGenerators/lhapdf/6.5.3/${platform}/share/LHAPDF:/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current
    export OL_PREFIX=${base}/${LCG}/MCGenerators/openloops/2.1.2/${platform}/
    
    # Set LIBRARY_PATH, for finding librariries during buildtime and not just runime
    # Sherpa needs openmpi (from LCG stack), and libpciaccess which is not available in the LCG stack
    # libpciaccess-devel needs to be installed on the host system when compiling loops for Sherpa
    export LIBRARY_PATH=$LD_LIBRARY_PATH:$LIBRARY_PATH
}

source_sherpa "$@"
Sherpa --version
