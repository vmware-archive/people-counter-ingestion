import json

class CapturedData():
    """
    A class used to hold the values returned from an analytics platform
    """
    def __init__(self, creation_timestamp, device_id=None, upload_file_path=None):
        self.device_id = device_id
        self.creation_timestamp = creation_timestamp
        self.upload_file_path = upload_file_path
        self.storage_path = ""

    def to_json(self):
        x = {
            "type": "data",
            "deviceID": self.device_id,
            "filePath": self.storage_path,
            "creationTimestamp": self.creation_timestamp
        }
        return json.dumps(x)

    def upload_file_exists(self):
        if self.upload_file_path is None:
            return False
        return True
    
    def get_upload_file_path(self):
        return self.upload_file_path

    def set_storage_path(self, storage_path):
        self.storage_path = storage_path

    def set_device_id(self, device_id):
        self.device_id = device_id
        