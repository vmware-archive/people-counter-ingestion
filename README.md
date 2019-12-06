# people-counter-ingestion

Ingestion service for the People Counter Demo application. It is written in Python and captures images on an interval from the Raspberry Pi 3 Camera and uploads them to Minio to make them available for inference. The daemon uses MQTT to advertise that a new image has been uploaded to Minio where other microservices can access them.

## Prerequisites

The application relies on the Raspberry Pi camera and the Python library associated with it. You must enable the Raspberry Pi camera library by following the instructions on the link below:

[Camera Configuration](https://www.raspberrypi.org/documentation/configuration/camera.md)

You must have access to the following:

* Pulse IoT Center Server
* MQTT Server

## Configuration

The code comes with an Ansible playbook you can run to automatically configure the target Raspberry Pi system. Run the Ansible playbook by following the instructions in the [README](configure/ansible-role-image-ingestion-service/README.md).

## Running the Ingestion Daemon

When testing or making changes to the code, you can run the ingestion daemon with the defaults plus the required parameters by executing the following command:

```bash
python3 image_capture_daemon.py -d [insert file system directory ] -n [insert MQTT user] -p [insert MQTT password] -s [insert MQTT host] -e [insert MQTT port] -v [insert Pulse IoT Center UUID for the device] -b [object store module arguments]
```

***Note***: If you wish to use a different MQTT topic or want to change the behavior of the application without making code changes, run the `python3 image_capture_daemon.py --help` to get a list of all the options available.

### Using the Minio Object Store Module

The code was design with flexibility in mind. You can upload the images to any object store you wish as long as you can implement the [object store interface](object_store/object_store.py). A working example implementation is included in the project using Minio. To use the included Minio module, run the following command:

```bash
python3 image_capture_daemon.py -n myuser -p mypassword -s my.mqtthost.com -e 18809 -v mydeviceid -b '{"host": "my-minio-host:9000", "accessKey": "mykey", "secretKey": "mysecret", "bucketName": "people-counter-images", "httpsEnabled": false}'
```

***Note***: make sure to replace the information with the one that matches your environment.

## Build

The daemon is ran as a Linux service using a unit file. In order for the unit file to work correctly, a few variables are required. The variables are loaded via a configuration file. To get the configuration file ready, follow the instructions below:

* Copy the [people-counter-ingestion.conf.sample](people-counter-ingestion.conf.sample) to the same folder it is located in but change the name to `people-counter-ingestion.conf`
* Update the variables with those matching your environment.

Pulse IoT Center is used as the primary way to deploy the application to a production-like system. In order to do that, we must first build the Pulse package. Instructions on how to build a Pulse package can be found in the [Pulse User Guide](https://docs.vmware.com/en/VMware-Pulse-IoT-Center/2019.11/iotc-user-guide.pdf). After following the instructions there to setup your build server, you can run the following commands to create the package:

```bash
cd build
package-cli package create people-counter-ingestion-service-spec.yml
package-cli upload package people_counter_ingestion_service-1.0.0.iotcp https://insert-pulse-hostname
```

## Deploy

Once you have created the Pulse package and uploaded it to Pulse IoT Center, follow the instructions in the Pulse User Guide mentioned above to create a campaign and deploy the package to the Raspberry Pi.

When the campaign finishes execution, you can check your MQTT image-related messages. You should see messages being published on the topic `image/latest`:

```bash
{"deviceID": "60261e35-7c0c-4ad2-9543-43855f35a1e6", "imagePath": "people-counter-images/image2019-12-03-23-43-57.jpg", "creationTimestamp": 1575416638.74405}
```

We should also start seeing the actual image files uploaded to the object store specified in the configurations.

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
