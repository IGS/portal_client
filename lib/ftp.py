"""
Handles the downloading of data from FTP sites.
"""

import os
import logging
from ftplib import FTP

class PortalFTP:
    """
    The PortalFTP class provides for simple retrieval of data from FTP servers.
    """
    def __init__(self, blocksize=100000):
        """
        Constructor for the PortalFTP class.
        """
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)

        self.logger.addHandler(logging.NullHandler())

        self.blocksize = blocksize

        # A dictionary to store connections keyed by hostname
        self.connections = {}

    def download_file(self, url, local_path, progress_bar=None):
        """
        Given a remote FTP file's URL, download it and save it to the specified
        local path.
        """
        self.logger.debug("In download_file. URL: %s", url)

        if not url.startswith('ftp://'):
            raise Exception("Invalid FTP url. Must start with ftp://")

        # If we only have part of a file, get the new start position
        current_byte = 0

        # Need to pull the size without the potential bytes buffer
        remote_file_size = self._get_file_size(url)

        if os.path.exists(local_path):
            current_byte = os.path.getsize(local_path)

            if current_byte < remote_file_size:
                self.logger.warning("The local file is smaller than the remote one.")
                self._handle_chunked_download(url, local_path, current_byte, remote_file_size, progress_bar)
            elif current_byte > remote_file_size:
                self.logger.warning("The local file is LARGER than the remote one! Skipping.")
            else:
                # sizes must be equal
                self.logger.info("File already present. Skipping.")
        else:
            self._handle_chunked_download(url, local_path, current_byte, remote_file_size, progress_bar)

    def _handle_chunked_download(self, url, file_name, current_byte, file_size, progress_bar=None):
        self.logger.debug("In _handle_chunked_download: %s", url)

        res = self._get_url_obj(url)

        blocksize = self.blocksize

        if progress_bar is not None:
            progress_bar.reset(total=file_size)
            progress_bar.update(current_byte)

        with open(file_name, 'ab') as file:

            self._get_buffer(res, current_byte, file_size, file, progress_bar)


    def _get_ftp_connection(self, host):
        self.logger.debug("In _get_ftp_connection. Host: %s", host)

        if host not in self.connections:
            ftp = FTP(host)
            ftp.login()
            self.connections[host] = ftp

        conn = self.connections[host]

        return conn

    # Get a network object of the file that can be iterated over.
    # Arguments:
    # url = path to location of the file on the web
    # current_byte = The byte position to retrieve data from
    def _get_url_obj(self, url):
        self.logger.debug("In _get_url_obj: %s", url)

        parsed = self._parse_ftp_url(url)
        ftp = self._get_ftp_connection(parsed['host'])

        # Make sure there's something there
        if list(ftp.nlst(parsed['file_path'])):
            file_str = "RETR {0}".format(parsed['file_path'])

            def get_data(callback, blocksize, start_pos):
                ftp.retrbinary(file_str, callback, blocksize=blocksize, rest=start_pos)

            return get_data

        # If made it here, no network object established
        return "error"

    # Function to retrieve the file size.
    # Arguments:
    # url = path to location of file on the web
    def _get_file_size(self, url):
        self.logger.debug("In _get_file_size.")

        parsed = self._parse_ftp_url(url)
        ftp = self._get_ftp_connection(parsed["host"])
        ftp.sendcmd("TYPE i")
        file_size = ftp.size(parsed["file_path"])

        self.logger.debug("Size is: %s", str(file_size))

        return file_size

    # Function to retrieve a particular set of bytes from the file.
    # Arguments:
    # res = network object created by get_url_obj()
    def _get_buffer(self, res, start_pos, max_range, file, progress_bar=None):
        self.logger.debug("In _get_buffer.")

        # The Python ftplib requires transfer to pass to a callback function,
        # using this to break up the download into pieces.
        def callback(data):
            file.write(data)

            if progress_bar is not None:
                progress_bar.update(len(data))

        res(callback, self.blocksize, start_pos)

        return None

    def _parse_ftp_url(self, url):
        self.logger.debug("In _parse_ftp_url: %s", url)

        dest = url.split('//')[1]
        host = dest.split('/')[0]
        file_path = url.split(host)[1]

        return {'dest': dest, 'host': host, 'file_path': file_path}

