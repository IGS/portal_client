"""
Handles the downloading of data from Google Cloud Platform (Google Storage).
"""

import os
import logging
from google.cloud import storage
from os import path

class GCP:
    """
    The GCP class provides for simple retrieval of data from Google Storage.
    """
    def __init__(self, project_id):
        """
        Constructor for the GCP class.
        """
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)

        self.logger.addHandler(logging.NullHandler())

        self._project_id = project_id

        self.client = storage.Client(project=self._project_id)  # uses ADC


    @property
    def project_id(self):
        return self._project_id

    def download_file(self, gs_remote_path, local_path):
        """
        Given a remote GCP object's URL, starting with gs://, download it and
        save it to the specified local path.
        """
        self.logger.debug("In download_file.")

        # Get the bucket from the gs_remote_path, which should be in the
        # form of gs://bucket_name/path
        if gs_remote_path.startswith('gs://'):
            gs_remote_path = gs_remote_path[5:]
        else:
            raise Exception("Invalid google storage path. Must start with gs://")

        bucket_name, obj_path = gs_remote_path.split('/', 1)
        self.logger.debug("Bucket name: %s", bucket_name)
        self.logger.debug("Object path: %s", obj_path)

        bucket = self.client.bucket(bucket_name)

        blob = bucket.blob(obj_path)

        self.logger.info("Downloading %s to %s.", obj_path, local_path)

        blob.download_to_filename(local_path)
