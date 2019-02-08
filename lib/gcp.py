import os
import logging
from os import path
import sys

from google.cloud import storage

from google_auth_oauthlib import flow

class GCP(object):
    def __init__(self, project_id, client_secrets_path):
        """
        Constructor for the GCP class.
        """
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)

        self.logger.addHandler(logging.NullHandler())

        self.project_id = project_id

        if not (path.isfile(client_secrets_path) and os.access(client_secrets_path, os.R_OK)):
            raise Exception("File {} doesn't exist or isn't readable.".format(client_secrets_path))

        self.logger.debug("File {} exists as a file and is readable.".format(client_secrets_path))

        self.client_secrets_path = client_secrets_path

        appflow = flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_path,
            scopes = ['https://www.googleapis.com/auth/devstorage.read_only']
        )

        self.logger.debug("Running flow for Google authorization.")
        appflow.run_console()

        self.credentials = appflow.credentials


    def client_secrets_path(self):
        return self.client_secrets_path

    def project_id(self):
        return self.project_id

    # remote_path = 'biccn/grant/cemba/ecker/chromatin/scell/raw/1B/CEMBA180118_1B/Undetermined_S0_L001.fastq.tar'
    def download_file(self, gs_remote_path, local_path):
        self.logger.debug("In download_file.")

        # TODO: Get the bucket from the gs_remote_path, which should be in the
        # form of gs://bucket_name/path
        if gs_remote_path.startswith('gs://'):
            gs_remote_path = gs_remote_path[5:]
        else:
            raise Exception("Invalid google storage path. Must start with gs://")

        bucket_name = gs_remote_path.split('/')[0]

        self.logger.debug("Bucket name: {}".format(bucket_name))

        bucket_length = len(bucket_name)
        obj_path = gs_remote_path[bucket_length + 1:]

        self.logger.debug("Object path: {}".format(obj_path))

        client = storage.Client(project=self.project_id, credentials=self.credentials)

        bucket = client.get_bucket(bucket_name)

        blob = bucket.blob(obj_path)

        self.logger.info("Downloading {} to {}.".format(obj_path, local_path))

        blob.download_to_filename(local_path)
