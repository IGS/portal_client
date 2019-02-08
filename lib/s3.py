import os
import logging
from os import path
import sys

import boto
from boto.utils import get_instance_metadata

class S3(object):
    def __init__(self, blocksize=100000):
        """
        Constructor for the S3 class.
        """
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)

        self.logger.addHandler(logging.NullHandler())

        self.blocksize = blocksize

        # Estalish an anonymous connection to S3 with boto
        self.connection = boto.connect_s3(anon=True)

    def download_file(self, s3_remote_path, local_path):
        self.logger.debug("In download_file.")

        if not s3_remote_path.startswith('s3://'):
            raise Exception("Invalid Amazon S3 path. Must start with s3://")

        # If we only have part of a file, get the new start position
        current_byte = 0

        # Need to pull the size without the potential bytes buffer
        remote_file_size = self._get_file_size(s3_remote_path)
        self.logger.debug("Remote file size: {}".format(remote_file_size))

        if os.path.exists(local_path):
            current_byte = os.path.getsize(local_path)

            if current_byte < remote_file_size:
                self.logger.warn("The local file is smaller than the remote one.")
                self._handle_chunked_download(s3_remote_path, local_path, current_byte, remote_file_size)
            elif current_byte > remote_file_size:
                self.logger.warn("The local file is LARGER than the remote one! Skipping.")
            else:
                # sizes must be equal
                self.logger.info("File already present. Skipping.")
        else:
            self._handle_chunked_download(s3_remote_path, local_path, current_byte, remote_file_size)


    def _handle_chunked_download(self, url, tmp_file_name, current_byte, file_size):
        self.logger.debug("In _handle_chunked_download.")

        res = self._get_url_obj(url)

        blocksize = self.blocksize

        with open(tmp_file_name, 'ab') as filehandle:
            print(
                "Downloading file from AWS S3: {0} | total bytes = {1}"
                    .format(tmp_file_name, file_size)
            )

            while True:
                if blocksize > file_size:
                    self._generate_status_message("block size greater than " + \
                        "total file size, pulling in entire file.")

                buf = self._get_buffer(res, current_byte, file_size, filehandle)

                # Note: only HTTP and S3 make it beyond this point
                if not buf:
                    break

                filehandle.write(buf)

                current_byte += len(buf)

                msg = "{0}  [{1:.2f}%]".format(
                    current_byte,
                    current_byte * 100 / file_size
                )

                self._generate_status_message(msg)

    # Function to retrieve a particular set of bytes from the file.
    # Arguments:
    # res = network object created by get_url_obj()
    # block_size = number of bytes to be considered a chunk to allow interrupts/resumes
    # start_pos = position to start at
    # max_range = maximum value to use for the range, same as the file's size
    # file = file handle to write out to
    def _get_buffer(self, res, start_pos, max_range, file):
        if start_pos >= max_range:
            return None # exit the while loop

        headers = {}

        # Offset by 1 since bytes are 0-based
        range_end = start_pos + self.blocksize - 1

        headers['Range'] = 'bytes={0}-'.format(start_pos)

        if range_end <= max_range:
            headers['Range'] += "{0}".format(range_end)

        return res.get_contents_as_string(headers=headers)

    # Get the key object from S3.
    # Arguments:
    # url = path to location of file on the web
    def _s3_get_key(self, url):
        self.logger.debug("In _s3_get_key.")

        url = url.lstrip('s3://')
        bucket_name = url.split('/', 1)[0]
        key = url.split('/', 1)[1]

        self.logger.debug("Bucket name: {}".format(bucket_name))
        bucket = self.connection.get_bucket(bucket_name)

        return bucket.get_key(key)

    # Get a network object of the file that can be iterated over.
    # Arguments:
    # url = path to location of file on Amazon S3
    def _get_url_obj(self, url):
        self.logger.debug("In _get_url_obj: {}".format(url))

        res = self._s3_get_key(url)

        # Assume we errored...
        return_value = "error"

        if res:
            # But, maybe we didn't...
            return_value = res

        return return_value

    # Function to retrieve the file size.
    # Arguments:
    # url = path to location of file on the web
    def _get_file_size(self, url):
        self.logger.debug("In _get_file_size.")

        key = self._s3_get_key(url)

        return key.size

    # Function to output a status message to the user.
    # Argument:
    # message = the string to temporarily output to the user
    def _generate_status_message(self, message):
        status = message
        # backspace everything
        status = status + chr(8) * (len(status) + 1)
        print("\r{0}".format(status), end="")

