"""
Handles the downloading of data from Google Cloud Platform (Google Storage).
"""

import os
import logging
from google.cloud import storage
from google.api_core import exceptions as gcp_exceptions
from os import path

class GCP:
    """
    The GCP class provides for simple retrieval of data from Google Storage.
    """
    def __init__(self, project_id=None, blocksize=100000):
        """
        Constructor for the GCP class.
        """
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)

        self.logger.addHandler(logging.NullHandler())

        self._project_id = project_id
        self.blocksize = blocksize

        self.client = storage.Client(project=self._project_id)  # uses ADC


    @property
    def project_id(self):
        return self._project_id

    def download_file(self, gs_remote_path, local_path, progress_bar=None):
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

        bucket = self.client.bucket(bucket_name, user_project=self._project_id)

        blob = bucket.blob(obj_path)

        self.logger.info("Downloading %s to %s.", obj_path, local_path)

        try:
            blob.reload()
        except gcp_exceptions.NotFound as e:
            raise Exception(f"File not found: gs://{bucket_name}/{obj_path}: {e.message}")
        except gcp_exceptions.Forbidden as e:
            raise Exception(f"Permission denied: gs://{bucket_name}/{obj_path}: {e.message}")
        except gcp_exceptions.BadRequest as e:
            if "requester pays" in str(e).lower() or "user project" in str(e).lower():
                raise Exception(
                    f"Bucket gs://{bucket_name} requires a billing project. "
                    f"Please provide --google-project-id: {e.message}"
                )
            raise

        file_size = blob.size

        if progress_bar is not None:
            progress_bar.reset(total=file_size)

        with blob.open("rb") as remote_file:
            with open(local_path, "wb") as local_file:
                while True:
                    chunk = remote_file.read(self.blocksize)
                    if not chunk:
                        break
                    local_file.write(chunk)

                    if progress_bar is not None:
                        progress_bar.update(len(chunk))
