#!/bin/bash
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: BSD-2-Clause
#

# Start the service and enable it to restart when the machine boots up
systemctl daemon-reload
systemctl start people-counter-ingestion
systemctl enable people-counter-ingestion
