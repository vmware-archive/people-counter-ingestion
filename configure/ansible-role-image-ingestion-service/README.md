# ansible-role-image-ingestion-service

The purpose of this repository is to automate the configuration of a Raspberry Pi to run the image ingestion microservice.

## Getting Started

Clone this repository into the machine you wish to use to run the Ansible playbook. Going forward, we will call this machine the Ansible controller.

### Prerequisites

The following needs to be installed on the Ansible controller:

* Ansible 2.7

The following needs to be installed on the Raspberry Pi before running the playbook:

* SSH daemon with remote access enabled
* Python 3.7.2

You must have access to an object store where the images taken from the Raspberry Pi will be uploaded to. The playbook was tested against Minio but Amazon S3 should work as well.

### Configuration

Once you have the repository cloned into the Ansible controller, then make a copy of the `hosts.sample` file to the same folder but name it `hosts`. Be sure to update the file based on the number of devices that you wish to configure and fill in the IP addresses corresponding to each device. A sample of the format to use to list out the devices is included in the sample file.

Next, make a copy of the `group_vars/image_ingestion_service.sample` file to the same folder it in but name it `image_ingestion_service`. Update the new file with the with the information for you object store.

## Running the Playbook

To execute the playbook, run the following command from the root directory:

```bash
ansible-playbook -i hosts site.yml --ask-pass --ask-become-pass
```

The playbook will ask you for the password that belongs to the `remote_user` account you specified and the sudo password for the device if it
is different than the one for the `remote_user`. If your SSH password for the `remote_user` is the same as the sudo password for the device edge, then you can just press enter when it asks you for it.

Once the playbook finishes executing, you can verify the results by checking your Minio instance for the bucket name you specified in the `group_vars/image_ingestion_service` file.

## Authors

* **Luis M. Valerio** - *Initial work*
