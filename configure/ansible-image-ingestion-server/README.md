# ansible-role-apache

The purpose of this repository is to automate the installation of the an Apache web server on a Debian system for hosting images.

***Note**: In Pulse IoT Center, device edges are called gateways.

## Getting Started

Clone this repository into the machine you wish to use to run the Ansible playbook.
Make sure the machine has SSH access to the Debian system.

### Prerequisites

The following needs to be installed on the Ansible control machine:

* Ansible 2.7

The following needs to be installed on the device edge(s):

* SSH daemon with remote access enabled
* Python 3.7.2

### Configuration

Once you have the repository cloned into the machine you are going to use as the Ansible controller, then make a copy of the `hosts.sample` file to the same folder but name it `hosts`. Be sure to update the file based on the number of devices that you wish to configure and fill in the IP addresses domain name corresponding to each device. A sample of the format to use to list out the devices is included in the sample file.

## Running the Playbook

To execute the playbook, run the following command from the root directory:

```bash
ansible-playbook -i hosts image-ingestion-server.yml --ask-pass --ask-become-pass
```

The playbook will ask you for the password that belongs to the `remote_user` account you specified and the sudo password for the device if it
is different than the one for the `remote_user`. If your SSH password for the `remote_user` is the same as the sudo password for the device edge, then you can just press enter when it asks you for it.

Once the playbook finishes executing, you can verify the results by entering the IP address of the device in your browser. You should see the home page for Apache.

## Authors

* **Luis M. Valerio** - *Initial work*

## License

This project is licensed under the BSD 2-Clause License - see the [LICENSE.txt](LICENSE.txt) file for details
