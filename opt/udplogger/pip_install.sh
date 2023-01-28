#!/bin/bash
echo "Checking and installing required PIP packages"

PKG_OK=$(dpkg-query -W --showformat='${Status}\n' python3-pip|grep "install ok installed")
echo Checking for pip3: $PKG_OK
if [ "" == "$PKG_OK" ]; then
    echo "No pip3. Setting up pip3."
    sudo apt-get --force-yes --yes install python3-pip
fi

#echo "Installing required python packages"
#PKG_OK=$(sudo -H pip3 freeze| grep -i "socket==")
#echo Checking for socket: $PKG_OK
#if [ "" == "$PKG_OK" ]; then
#    echo "No socket. Setting up socket."
#    sudo -H pip3 install socket
#fi

echo "Ready"
