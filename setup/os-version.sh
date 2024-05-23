#!/bin/bash

if ! command -v lsb_release &> /dev/null
then
    source /etc/os-release
    distro=$NAME
    os_version=$VERSION_ID
else
    distro=$(lsb_release -i | cut -f2)
    os_version=$(lsb_release -r | cut -f2)
fi
distro=${distro//[[:space:]]/}
distro="${distro//Linux/}"
distro="${distro//linux/}"
echo "Running on $distro Version $os_version..."
