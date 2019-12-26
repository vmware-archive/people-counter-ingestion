#!/bin/bash
#
# Copyright © 2019 VMware, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: BSD-2-Clause
#

if [ -z "$DATADIR" ]
then
    DATADIR=$PWD
fi

echo "Working directory: $DATADIR" | systemd-cat -t ingestion-service-install -p info

# # Check if a user exists. Create it if it does not.
# if id iotadmin > /dev/null 2>&1; then
#     echo "iotadmin user already exists. Will not create."
# else
#     useradd -g video iotadmin
#     if [ $? -eq 0 ]; then
#         echo "User iotadmin added successfully" | systemd-cat -t ingestion-service-install -p info
#     else
#         echo "Failed to create iotadmin user" | systemd-cat -t ingestion-service-install -p emerg
#         exit 1
#     fi
# fi

echo "Copying python code to /opt/vmware/people-counter-ingestion-service..." | systemd-cat -t ingestion-service-install -p info
install -D -C -m 775 -o iotadmin -g video $DATADIR/image_capture_daemon.py /opt/vmware/people-counter-ingestion-service/image_capture_daemon.py
install -D -C -m 775 -o iotadmin -g video $DATADIR/object_store.py /opt/vmware/people-counter-ingestion-service/object_store/object_store.py
install -D -C -m 775 -o iotadmin -g video $DATADIR/minio_object_store.py /opt/vmware/people-counter-ingestion-service/object_store/providers/minio_object_store.py
install -D -C -m 775 -o iotadmin -g video $DATADIR/people-counter-ingestion.conf /opt/vmware/people-counter-ingestion-service/people-counter-ingestion.conf
install -D -C -m 775 -o iotadmin -g video $DATADIR/data.py /opt/vmware/people-counter-ingestion-service/data_source/data.py
install -D -C -m 775 -o iotadmin -g video $DATADIR/data_source.py /opt/vmware/people-counter-ingestion-service/data_source/data_source.py
install -D -C -m 775 -o iotadmin -g video $DATADIR/raspberrypi_camera.py /opt/vmware/people-counter-ingestion-service/data_source/connected_devices/raspberrypi_camera.py


echo "Copying unit file to /etc/systemd/system/...." | systemd-cat -t ingestion-service-install -p info
install -C -m 775 -o root -g root $DATADIR/people-counter-ingestion.service /etc/systemd/system
