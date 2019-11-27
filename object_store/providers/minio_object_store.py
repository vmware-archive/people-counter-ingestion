from object_store.object_store import ObjectStoreInterface
from minio import Minio
from minio.error import ResponseError
import logging
import json
import os

class MinioObjectStore(ObjectStoreInterface):
    
    def initialize(self, jsonArgs):
        # The function should initialize any connections that need
        # to be made or any variables that will be required
        format = "%(asctime)s - %(levelname)s: %(threadName)s - %(message)s"
        logging.basicConfig(format=format, level=logging.DEBUG,
                        datefmt="%H:%M:%S")
        args = json.loads(jsonArgs)

        # Extract variables from JSON
        self.host = args['host']
        self.access_key = args['accessKey']
        self.secret_key = args['secretKey']
        self.https_enabled = args['httpsEnabled']
        if 'bucketName' in args:
            self.bucket_name = args['bucketName']

        # Instantiate client 
        self.minio_client = Minio(
            self.host, 
            access_key=self.access_key, 
            secret_key=self.secret_key, 
            secure=self.https_enabled
            )

        self.validate()

    def upload(self, filepath, bucket_name = None):
        """
        Uploads a file to Minio.

        The function uploads a file from the path in the filesystem specified and uploads
        it to a bucket in Minio.

        Parameters:
        filepath (string): The absolute path of the file to upload
        bucket_name (string): Optional argument to indicate the bucket to use to upload the file

        Returns:
        string: The location of the image in Minio
        """

        bucket = ""
        if bucket_name is not None:
            bucket = bucket_name
        elif self.bucket_name is not None:
            bucket = self.bucket_name
        else:
            raise Exception(
                "The instance variable bucket_name was not initialized. You must either initialize it or pass it to the function")

        # Upload file to Algorithmia
        filename = os.path.basename(filepath)
        logging.debug("Uploading file '%s' to bucket '%s'", filepath, bucket)
        try:
            self.minio_client.fput_object(
                bucket, 
                filename, 
                filepath
                )
        except ResponseError as err:
            logging.error("Upload of file '%s' failed", filepath)
            raise err
        logging.debug("Upload of file was successful")

        return bucket + '/' + filename
    
    def download(self, filename, download_path, bucket_name = None):
        # Downloads an object from Minio

        bucket = ""
        if bucket_name is not None:
            bucket = bucket_name
        elif self.bucket_name is not None:
            bucket = self.bucket_name
        else:
            raise Exception(
                "The instance variable bucket_name was not initialized. You must either initialize it or pass it to the function")

        logging.debug("Downloading file '%s' from bucket '%s'", filename, bucket)
        try:
            self.minio_client.fget_object(
                bucket, 
                filename, 
                download_path
                )
        except ResponseError as err:
            logging.error("Download of file '%s' failed", filename)
            raise err
        logging.debug('File download was successful')

    def delete(self, filename, bucket_name = None):
        # Deletes a file from Minio

        bucket = ""
        if bucket_name is not None:
            bucket = bucket_name
        elif self.bucket_name is not None:
            bucket = self.bucket_name
        else:
            raise Exception(
                "The instance variable bucket_name was not initialized. You must either initialize it or pass it to the function")

        logging.debug("Deleting file '%s' from bucket '%s'", filename, bucket)
        try:
            self.minio_client.remove_object(
                bucket, 
                filename
                )
        except ResponseError as err:
            logging.error("Deletion of file '%s' failed", filename)
            raise err
        logging.debug('Deletion of file was successful')

    def list_objects(self, bucket_name = None):
        bucket = ""
        if bucket_name is not None:
            bucket = bucket_name
        elif self.bucket_name is not None:
            bucket = self.bucket_name
        else:
            raise Exception(
                "The instance variable bucket_name was not initialized. You must either initialize it or pass it to the function")

        objects = self.minio_client.list_objects(bucket)
        object_list = []
        for obj in objects:
            object_list.append((obj.object_name, obj.last_modified))

        return object_list

    ######################HELPER METHODS########################

    def validate(self):
        # The function should hold any validation that
        # needs to be run before the class can be used

        if self.bucket_name is not None:
            try:
                self.minio_client.bucket_exists(self.bucket_name)
            except ResponseError as err:
                logging.error("Validation failed for the input variable 'bucketName' with value '%s'", self.bucket_name)
                raise err
            
            logging.debug("Testing file upload with test file: %s to Minio", os.path.realpath(__file__))
            self.upload(os.path.realpath(__file__))


            logging.debug('Starting test file deletion')
            self.delete(os.path.basename(__file__))
            