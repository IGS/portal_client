"""
Handles the downloading of data from Google Cloud Platform (Google Storage).
"""

import os
from os import path

import logging

from google.cloud import storage
from google_auth_oauthlib import flow

class GCP:
    """
    The GCP class provides for simple retrieval of data from Google Storage.
    """
    def __init__(self, project_id, client_secrets_path):
        """
        Constructor for the GCP class.
        """
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)

        self.logger.addHandler(logging.NullHandler())

        self._project_id = project_id

        if not (path.isfile(client_secrets_path) and os.access(client_secrets_path, os.R_OK)):
            raise Exception("File {} doesn't exist or isn't readable.".format(client_secrets_path))

        self.logger.debug("File %s exists as a file and is readable.", client_secrets_path)

        self._client_secrets_path = client_secrets_path

        appflow = flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_path,
            scopes=['https://www.googleapis.com/auth/devstorage.read_only']
        )

        self.logger.debug("Running flow for Google authorization.")
        appflow.run_console()

        self.credentials = appflow.credentials

    @property
    def client_secrets_path(self):
        return self._client_secrets_path

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

        bucket_name = gs_remote_path.split('/')[0]

        self.logger.debug("Bucket name: %s", bucket_name)

        bucket_length = len(bucket_name)
        obj_path = gs_remote_path[bucket_length + 1:]

        self.logger.debug("Object path: %s", obj_path)

        client = storage.Client(project=self.project_id, credentials=self.credentials)

        bucket = client.get_bucket(bucket_name)

        blob = bucket.blob(obj_path)

        self.logger.info("Downloading %s to %s.", obj_path, local_path)

        blob.download_to_filename(local_path)
