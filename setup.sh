#!/bin/bash
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: BSD-2-Clause
#

read -sp 'Enter password to create iotadmin user:' userpass
echo
useradd -p $(echo $userpass | openssl passwd -1 -stdin) -g video iotadmin
if [ $? -eq 0 ]; then
    echo "User iotadmin added successfully"
else
    echo "Failed to create iotadmin user"
    exit 1
fi

echo "Copying python code to /opt/vmware/people-counter-ingestion-service..."
mkdir -p /opt/vmware/people-counter-ingestion-service
install -C -m 775 -o iotadmin -g video image_capture_daemon.py /opt/vmware/people-counter-ingestion-service

echo "Copying unit file to /etc/systemd/system/...."
install -C -m 775 -o root -g root people-counter-ingestion.service /etc/systemd/system