# People Counter Ingestion Service

Ingestion service for the People Counter Demo application. It is written in Python and captures images on an interval from the Raspberry Pi 3 Camera and puts them in a folder on the filesystem.

## Running the Ingestion Daemon

To run the ingestion daemon with the defaults plus the required parameters, execute the following command:

```bash
python3 image_capture_daemon.py -d [insert file system directory ] -n [insert MQTT user] -p [insert MQTT password] -s [insert MQTT host] -e [insert MQTT port] -v [insert Pulse IoT Center UUID for the device]
```
