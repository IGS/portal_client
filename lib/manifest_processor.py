"""
Handles the downloading of the manifest contents.
"""

import hashlib
import logging
import os
import shutil
import aspera

from portal_http import PortalHTTP
from s3 import S3
from ftp import PortalFTP

from boto.utils import get_instance_metadata

class ManifestProcessor(object):

    def __init__(self, username=None, password=None, google_client_secrets=None,
                 google_project_id=None, blocksize=100000):
        """
        Constructor for the ManifestProcessor class.
        """
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)

        self.logger.addHandler(logging.NullHandler())

        # Create the HTTP client
        self.http_client = PortalHTTP(blocksize=blocksize)

        # Create the FTP client
        self.ftp_client = PortalFTP(blocksize=blocksize)

        # Create the AWS S3 client
        self.aws_s3 = S3(blocksize=blocksize)

        self.blocksize = blocksize

        self.username = username

        self.password = password

        # By default, we will check MD5 checksums after each file is
        # retrieved/downloaded.
        self.validation = True

        if google_client_secrets is not None and google_project_id is not None:
            self.logger.info("Create GCP client.")
            from gcp import GCP
            self.gcp_client = GCP(google_project_id, google_client_secrets)

    def _get_fasp_obj(self, url, file_name):
        self.logger.debug("In _get_fasp_obj: %s", url)

        if url.startswith('fasp://'):
            url = url[7:]

        self.logger.debug("URL: %s", url)

        server = url.split('/')[0]
        self.logger.debug("Aspera server: %s", server)

        remote_path = url
        remote_path = remote_path.lstrip(server)
        self.logger.debug("Remote path: %s", remote_path)

        result = None

        try:
            success = aspera.download_file(server, self.username, self.password,
                                           remote_path, file_name)

            if not success:
                self.logger.error("Aspera transfer failed.")
                result = "error"
        except Exception as e:
            self.logger.error(e)
            result = "error"

        self.logger.debug("Returning %s", result)

        return result

    def _get_gcp_obj(self, url, file_name):
        self.logger.debug("In _get_gcp_obj: %s", url)

        if not url.startswith('gs://'):
            self.logger.error("Detected an invalid GCP url.")
            raise Exception("GCP URLs must begin with gs://")

        result = None

        try:
            self.gcp_client.download_file(url, file_name)
        except Exception as e:
            self.logger.error(e)
            result = "error"

        self.logger.debug("Returning %s", result)

        return result

    def _get_ftp_obj(self, url, file_name):
        self.logger.debug("In _get_ftp_obj: %s", url)

        if not url.startswith('ftp://'):
            self.logger.error("Detected an invalid FTP url.")
            raise Exception("FTP URLs must begin with ftp://")

        result = None

        try:
            self.ftp_client.download_file(url, file_name)
        except Exception as e:
            self.logger.error(e)
            result = "error"

        self.logger.debug("Returning %s", result)

        return result

    def _get_http_obj(self, url, file_name):
        self.logger.debug("In _get_http_obj: %s", url)

        if not (url.startswith('http://') or url.startswith('https://')):
            self.logger.error("Detected an invalid HTTP/HTTPS url.")
            raise Exception("HTTP URLs must begin with http:// or https://")

        result = None

        try:
            self.http_client.download_file(url, file_name)
        except Exception as e:
            self.logger.error(e)
            result = "error"

        self.logger.debug("Returning %s", result)

        return result

    def _get_s3_obj(self, url, file_name):
        self.logger.debug("In _get_s3_obj: %s", url)

        if not url.startswith('s3://'):
            self.logger.error("Detected an invalid Amazon S3 url.")
            raise Exception("S3 URLs must begin with s3://")

        result = None

        try:
            self.aws_s3.download_file(url, file_name)
        except Exception as e:
            self.logger.error(e)
            result = "error"

        self.logger.debug("Returning %s", result)

        return result

    def disable_validation(self):
        """
        Method to turn off MD5 checksum checking after a file is downloaded.
        For large files and particularly with manifests that contain large
        numbers of large files, disabling validation may significantly boost
        performance.
        """
        self.logger.debug("In disable_validation.")

        self.validation = False

    def download_manifest(self, manifest, destination, priorities):
        """
        Downloads each URL from the manifest.
        Arguments:
        manifest = manifest list
        destination = the destination directory to save downloaded files
        priorities = the protocol priorities
        """
        self.logger.debug("In download_manifest.")

        # Build a list of elements to indicate how many and why the files failed
        # 1 = no valid URL in manifest
        # 2 = URL exists, but not accessible at the location specified
        # 3 = MD5 check failed for file (file is corrupted or the wrong MD5 is attached to the file)
        failed_files = []

        # iterate over the manifest data structure, one ID/file at a time
        for mfile in manifest:

            url_list = self._get_prioritized_endpoint(mfile['urls'], priorities)

            # Handle private data or simply nodes that are not correct and lack
            # endpoint data
            if not url_list:
                print("No valid URL found in the manifest for file ID {0}".format(mfile['id']))
                failed_files.append(1)
                continue

            url_file_element = url_list[0].split('/')[-1]
            file_name = os.path.join(destination, url_file_element)

            # Only need to download if the file is not present
            if os.path.exists(file_name):
                self.logger.info("File %s already exists. Skipping.", file_name)
                failed_files.append(0)
            else:
                self.logger.debug("File not present. Proceeding.")

                tmp_file_name = "{0}.partial".format(file_name)

                res, endpoint = ("" for i in range(2))
                endpoints = []

                for url in url_list:
                    endpoint = url.split(':')[0].upper()
                    endpoints.append(endpoint)

                    if endpoint == "FASP":
                        res = self._get_fasp_obj(url, tmp_file_name)
                    elif endpoint == "GS":
                        res = self._get_gcp_obj(url, tmp_file_name)
                    elif endpoint == "HTTP":
                        res = self._get_http_obj(url, tmp_file_name)
                    elif endpoint == "FTP":
                        res = self._get_ftp_obj(url, tmp_file_name)
                    elif endpoint == "S3":
                        res = self._get_s3_obj(url, tmp_file_name)
                    else:
                        res = "error"

                    # If we get an error, continue to the next url in the list
                    if res == "error":
                        continue

                # If all attempts resulted in error, move on to next file
                if res == "error":
                    print("Skipping file ID {0} as none of the URLs {1} succeeded."
                          .format(mfile['id'], endpoints))
                    failed_files.append(2)
                    continue

                if self.validation:
                    # Now that the download is complete, verify the checksum,
                    # and then establish the final file
                    if self._checksum_matches(tmp_file_name, mfile['md5']):
                        self.logger.debug("Renaming %s to %s", tmp_file_name, file_name)
                        shutil.move(tmp_file_name, file_name)
                        failed_files.append(0)
                    else:
                        print("\r")
                        msg = "MD5 check failed for the file ID {0}. " + \
                              "Data may be corrupted."
                        print(msg.format(mfile['id']))
                        failed_files.append(3)
                else:
                    self.logger.debug(
                        "Skipping checksumming. Renaming %s to %s", tmp_file_name, file_name
                    )
                    shutil.move(tmp_file_name, file_name)
                    failed_files.append(0)

        return failed_files

    # Function to get the URL for the prioritized endpoint that the user requests.
    # Note that priorities can be a list of ordered priorities.
    # Arguments:
    # manifest_urls = the CSV set of endpoint URLs
    # priorities = priorities declared when calling client.py
    def _get_prioritized_endpoint(self, manifest_urls, priorities):
        self.logger.debug("In _get_prioritized_endpoint.")
        url_list = []

        urls = manifest_urls.split(',')
        eps = priorities.split(',')

        # If the user didn't provide a set of priorities, then prioritize based on
        # whether on an EC2 instance.
        if eps[0] == "":

            md = get_instance_metadata(timeout=0.5, num_retries=1)

            if md:
                eps = ['S3', 'HTTP', 'FTP']
            else:
                # If none provided, use this order
                eps = ['HTTP', 'FTP', 'S3']

        # Go through and build a list starting with the higher priorities first.
        for ep in eps:
            for url in urls:
                if url.startswith(ep.lower()):
                    url_list.append(url)

        return url_list

    # This function failing is largely telling that the data in OSDF for the
    # particular file's MD5 is not correct.
    # Arguments:
    # file_path = location of the file just downloaded which requires an integrity check
    # original_md5 = MD5 provided by OSDF data
    def _checksum_matches(self, file_path, original_md5):
        self.logger.debug("In checksum_matches. Checking %s.", file_path)
        md5 = hashlib.md5()

        # Read the file in chunks and build a final MD5
        with open(file_path, 'rb') as filehandle:
            for chunk in iter(lambda: filehandle.read(4096), b""):
                md5.update(chunk)

        valid = False
        if md5.hexdigest() == original_md5:
            valid = True

        self.logger.debug("Checksum valid? %s", str(valid))

        return valid
