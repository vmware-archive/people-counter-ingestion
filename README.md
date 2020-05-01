# people-counter-ingestion

Ingestion service for the People Counter Demo application. It is written in Python and captures images on an interval from the Raspberry Pi 3 Camera and uploads them to Minio to make them available for inference. The daemon uses MQTT to advertise that a new image has been uploaded to Minio where other microservices can access them.

## Prerequisites

The application relies on a camera device attached to the host. Make sure you have a camera connected to the machine running this code.

You must have access to the following services outside the code:

* MQTT Server
* MinIO Server

## Configuration

The code comes with an Ansible playbook you can run to automatically configure the target host system. Run the Ansible playbook by following the instructions in the [README](configure/ansible-role-image-ingestion-service/README.md).

## Build

The ingestion microservice is built using Docker. To build the docker image, use the following command:

```bash
sudo docker build --tag people-counter-ingestion .
```

***Note**: You can substitude the tag for whatever name you want to give to the image and even add a version.

<!-- The daemon is ran as a Linux service using a unit file. In order for the unit file to work correctly, a few variables are required. The variables are loaded via a configuration file. To get the configuration file ready, follow the instructions below:

* Copy the [people-counter-ingestion.conf.sample](people-counter-ingestion.conf.sample) to the same folder it is located in but change the name to `people-counter-ingestion.conf`
* Update the variables with those matching your environment. -->

## Run

To run the daemon after the Docker image is built, use the following command:

```bash
docker run --device=[insert host device index]:[insert index to map device inside container] --name [insert container name] people-counter-ingestion -n [insert MQTT user] -p [insert MQTT password] -s [insert MQTT host] -e [insert MQTT port] -v [insert Pulse IoT Center UUID for the device] -b [object store module arguments]
```

***Note***: If you wish to use a different MQTT topic or want to change the behavior of the application without making code changes, run the `python3 image_capture_daemon.py --help` to get a list of all the options available.

### Using the Minio Object Store Module

The code was design with flexibility in mind. You can upload the images to any object store you wish as long as you can implement the [object store interface](object_store/object_store.py). A working example implementation is included in the project using Minio. To use the included Minio module, run the following command:

```bash
docker run --device=/dev/video0:/dev/video0 -d --name ingestion-container people-counter-ingestion -n myuser -p mypassword -s my.mqtthost.com -e 1883 -v mydeviceid -b '{"host":"my-minio-host:9000","accessKey": "mykey","secretKey": "mysecret", "bucketName": "people-counter-images", "httpsEnabled": false}' -a '{"image_storage_folder": "/tmp", "device_index": 0}'
```

***Note***: make sure to replace the information with the one that matches your environment. Also, make sure the indext you map with the Docker `--device` flag matches the index you filled with the key `device_index` otherwise you'll see a failure.

## Contributing

The people-counter-ingestion project team welcomes contributions from the community. Before you start working with people-counter-ingestion, please
read our [Developer Certificate of Origin](https://cla.vmware.com/dco). All contributions to this repository must be
signed as described on that page. Your signature certifies that you wrote the patch or have the right to pass it on
as an open-source patch. For more detailed information, refer to [CONTRIBUTING.md](CONTRIBUTING.md).

## Authors

* [Luis M. Valerio](https://github.com/lvalerio)
* [Neeraj Arora](https://github.com/nearora)

## License

This project is licensed under the BSD 2-Clause License - see the [LICENSE.txt](LICENSE.txt) file for details
