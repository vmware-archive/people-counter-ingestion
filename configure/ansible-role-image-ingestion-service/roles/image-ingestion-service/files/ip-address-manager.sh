#!/bin/bash

# Find the IP address of the machine
ipaddress=$(hostname -I | awk '{print $1}')
echo The IP address of this machine is $ipaddress | systemd-cat -t ingestion-service-install -p info

# Take the IP address and replace the one in /etc/hosts
sed -i -e "s/.*raspberrypi$/$ipaddress     raspberrypi/g" test.txt