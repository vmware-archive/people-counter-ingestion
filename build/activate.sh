#!/bin/bash
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: BSD-2-Clause
#

# Start the service and enable it to restart when the machine boots up
sudo systemctl start people-counter-ingestion
sudo systemctl enable people-counter-ingestion
