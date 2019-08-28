#!/bin/bash

read -sp 'Enter password to create iotadmin user:\n' userpass

useradd -p $(echo $userpass | openssl passwd -1 -stdin) iotadmin
if [ $? -eq 0 ]; then
    echo "User iotadmin added successfully"
else
    echo "Failed to create iotadmin user"
fi

