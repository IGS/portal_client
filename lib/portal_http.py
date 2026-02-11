import os
import logging
from os import path
import urllib.request
import sys

class PortalHTTP(object):
    def __init__(self, blocksize=100000):
        """
        Constructor for the PortalHTTP class.
        """
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)

        self.logger.addHandler(logging.NullHandler())

        self.blocksize = blocksize

    def download_file(self, url, local_path, progress_bar=None):
        self.logger.debug("In download_file. URL: {}".format(url))

        # If we only have part of a file, get the new start position
        current_byte = 0

        # Need to pull the size without the potential bytes buffer
        remote_file_size = self._get_file_size(url)

        if os.path.exists(local_path):
            current_byte = os.path.getsize(local_path)

            if current_byte < remote_file_size:
                self.logger.warn("The local file is smaller than the remote one.")
                self._handle_chunked_download(url, local_path, current_byte, remote_file_size, progress_bar)
            elif current_byte > remote_file_size:
                self.logger.warn("The local file is LARGER than the remote one! Skipping.")
            else:
                # sizes must be equal
                self.logger.info("File already present. Skipping.")
        else:
            self._handle_chunked_download(url, local_path, current_byte, remote_file_size, progress_bar)

    def _handle_chunked_download(self, url, file_name, current_byte, file_size, progress_bar=None):
        self.logger.debug("In _handle_chunked_download: {}".format(url))

        res = self._get_url_obj(url, current_byte)

        blocksize = self.blocksize

        if progress_bar is not None:
            progress_bar.reset(total=file_size)
            progress_bar.update(current_byte)

        with open(file_name, 'ab') as file:

            while True:
                buffer = self._get_buffer(res)

                if not buffer: # note that only HTTP/S3 make it beyond this point
                    break

                file.write(buffer)

                current_byte += len(buffer)

                if progress_bar is not None:
                    progress_bar.update(len(buffer))

    # Get a network object of the file that can be iterated over.
    # Arguments:
    # url = path to location of the file on the web
    # current_byte = The byte position to retrieve data from
    def _get_url_obj(self, url, current_byte):
        self.logger.debug("In _get_url_obj: {}".format(url))

        http_header = {}
        http_header['Range'] = 'bytes={0}-'.format(current_byte)

        res = ""

        try:
            req = urllib.request.Request(url, headers=http_header)
            res = urllib.request.urlopen(req)
        except:
            res = ""

        if res:
            return res

        # If made it here, no network object established
        return "error"

    # Function to retrieve the file size.
    # Arguments:
    # url = path to location of file on the web
    def _get_file_size(self, url):
        self.logger.debug("In _get_file_size.")
        return int(urllib.request.urlopen(url).info()['Content-Length'])

    # Function to retrieve a particular set of bytes from the file.
    # Arguments:
    # res = network object created by get_url_obj()
    def _get_buffer(self, res):
        return res.read(self.blocksize)
