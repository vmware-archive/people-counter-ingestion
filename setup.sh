#!/bin/bash
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: BSD-2-Clause
#

if [ -z "$DATADIR" ]
then
    DATADIR=$PWD
fi

echo "Working directory: $DATADIR" | systemd-cat -t ingestion-service-install -p info

# Check if a user exists. Create it if it does not.
if id iotadmin > /dev/null 2>&1; then
    echo "iotadmin user already exists. Will not create."
else
    useradd -g video iotadmin
    if [ $? -eq 0 ]; then
        echo "User iotadmin added successfully" | systemd-cat -t ingestion-service-install -p info
    else
        echo "Failed to create iotadmin user" | systemd-cat -t ingestion-service-install -p emerg
        exit 1
    fi
fi

echo "Creating directory /opt/vmware/people-counter-ingestion-service..." | systemd-cat -t ingestion-service-install -p info
mkdir -p /opt/vmware/people-counter-ingestion-service

echo "Copying python code to /opt/vmware/people-counter-ingestion-service..." | systemd-cat -t ingestion-service-install -p info
install -C -m 775 -o iotadmin -g video $DATADIR/image_capture_daemon.py /opt/vmware/people-counter-ingestion-service

echo "Copying unit file to /etc/systemd/system/...." | systemd-cat -t ingestion-service-install -p info
install -C -m 775 -o root -g root $DATADIR/people-counter-ingestion.service /etc/systemd/system