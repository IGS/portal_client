# Handles the downloading of the manifest contents.

import aspera
import hashlib
import logging
import os
import shutil
import sys
import urllib
from ftplib import FTP

# Additional dependencies (get from pip)
import boto
from boto.utils import get_instance_metadata

# S3 connection.
S3_CONNS = {}

# FTP connections.
FTP_CONNS = {}

class ManifestProcessor(object):

    def __init__(self, username, password, blocksize=100000):
        """
        Constructor for the ManifestProcessor class.
        """
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)

        self.logger.addHandler(logging.NullHandler())

        self.blocksize = blocksize

        self.username = username

        self.password = password

    def _get_s3_connection(self):
        if 'S3' not in S3_CONNS:
            S3_CONNS['S3'] = boto.connect_s3(anon=True)
        return S3_CONNS['S3']


    def _get_ftp_connection(self, host):
        self.logger.debug("In _get_ftp_connection.")

        if host not in FTP_CONNS:
            ftp = FTP(host)
            ftp.login('portal_client')
            FTP_CONNS[host] = ftp
        return FTP_CONNS[host]

    def _parse_ftp_url(self, url):
        self.logger.debug("In _parse_ftp_url.")

        dest = url.split('//')[1]
        host = dest.split('/')[0]
        file_path = url.split(host)[1]

        return { 'dest': dest, 'host': host, 'file_path': file_path }

    # Function to download each URL from the manifest.
    # Arguments:
    # manifest = manifest list created by functions in convert_to_manifest.py
    # destination = set destination to place output declared when calling client.py
    # priorities = endpoint priorities established by get_prioritized_endpoint
    def download_manifest(self, manifest, destination, priorities):
        # build a list of elements to indicate how many and why the files failed
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

            file_name = "{0}/{1}".format(destination, url_list[0].split('/')[-1])

            if not os.path.exists(file_name): # only need to download if the file is not present

                tmp_file_name = "{0}.partial".format(file_name)

                res, endpoint = ("" for i in range(2))
                endpoints = []

                for url in url_list:
                    endpoint = url.split(':')[0].upper()
                    endpoints.append(endpoint)
                    if endpoint == "FASP":
                        res = self._get_fasp_obj(url, tmp_file_name)
                    else:
                        # If we only have part of a file, get the new start position
                        current_byte = 0
                        if os.path.exists(tmp_file_name):
                            current_byte = os.path.getsize(tmp_file_name)


                        # Need to try get the others to work like this, but for now HTTP
                        # is the only one that can pull bytes in chunks without needing to
                        # drop the connection.
                        http_header = {}
                        http_header['Range'] = 'bytes={0}-'.format(current_byte)

                        res = self._get_url_obj(url, endpoint, http_header)

                    # If we get an error, continue to the next url in the list
                    if res == "error":
                        continue

                # If all attempts resulted in error, move on to next file
                if res == "error":
                    print("Skipping file ID {0} as none of the URLs {1} succeeded."
                        .format(mfile['id'], endpoints))
                    failed_files.append(2)
                    continue

                if endpoint != "FASP":
                    self._handle_chunked_transfer(res, url, tmp_file_name, file_name, endpoint, current_byte)

                # Now that the download is complete, verify the checksum, and then
                # establish the final file
                if self._checksum_matches(tmp_file_name, mfile['md5']):
                    shutil.move(tmp_file_name, file_name)
                    failed_files.append(0)
                else:
                    print("\r")
                    msg = "MD5 check failed for the file ID {0}. " + \
                          "Data may be corrupted."
                    print(msg.format(mfile['id']))
                    failed_files.append(3)

            else: # file already done downloading
                failed_files.append(0)

        return failed_files

    def _handle_chunked_transfer(self, res, url, tmp_file_name, file_name, endpoint, current_byte):
        self.logger.debug("In _handle_chunked_transfer.")

        block_size = self.blocksize

        with open(tmp_file_name, 'ab') as file:
            # Need to pull the size without the potential bytes buffer
            file_size = self._get_file_size(url, endpoint)
            print(
                "Downloading file (via {0}): {1} | total bytes = {2}"
                    .format(endpoint, file_name, file_size)
            )

            while True:
                if block_size > file_size:
                    self._generate_status_message("block size greater than " + \
                        "total file size, pulling in entire file.")

                buffer = self._get_buffer(res, endpoint, block_size, current_byte, file_size, file)

                if not buffer: # note that only HTTP/S3 make it beyond this point
                    break

                file.write(buffer)

                current_byte += len(buffer)

                msg = "{0}  [{1:.2f}%]".format(
                    current_byte,
                    current_byte * 100 / file_size
                )
                self._generate_status_message(msg)

    def _get_fasp_obj(self, url, file_name):
        self.logger.debug("In _get_fasp_obj: {}".format(url))

        #url = url.lstrip('fasp://')
        if url.startswith('fasp://'):
            url = url[7:]

        self.logger.debug("url: {}".format(url))

        server = url.split('/')[0]
        self.logger.debug("Aspera server: {}".format(server))

        remote_path = url
        remote_path = remote_path.lstrip(server)
        self.logger.debug("Remote path: {}".format(remote_path))

        result = None

        try:
            aspera.download_file(server, self.username, self.password,
                remote_path, file_name)
        except Exception as e:
            self.logger.error(e)
            result = "error"

        self.logger.debug("Returning {}".format(result))

        return result

    # Get a network object of the file that can be iterated over.
    # Arguments:
    # url = path to location of file on the web
    # endpoint = HTTP/FTP/S3
    # http_header = HTTP range to pull from the file, the other endpoints require
    # this processing in the _get_buffer() method.
    def _get_url_obj(self, url, endpoint, http_header):
        self.logger.debug("In _get_url_obj: {}".format(url))

        if endpoint == "HTTP":
            res = ""

            try:
                req = urllib.request.Request(url, headers=http_header)
                res = urllib.request.urlopen(req)
            except:
                res = ""

            if res:
                return res

        if endpoint == "FTP":
            p = self._parse_ftp_url(url)
            ftp = self._get_ftp_connection(p['host'])

            # make sure there's something there
            if list(ftp.mlsd(p['file_path'])):
                file_str = "RETR {0}".format(p['file_path'])

                def get_data(callback, blocksize, start_pos):
                    ftp.retrbinary(file_str, callback, blocksize=blocksize, rest=start_pos)

                return get_data
        elif endpoint == "S3":
            res = self._s3_get_key(url)
            if res:
                return res

        # If made it here, no network object established
        return "error"

    # Function to retrieve the file size.
    # Arguments:
    # url = path to location of file on the web
    # endpoint = HTTP/FTP/S3
    def _get_file_size(self, url, endpoint):
        if endpoint == 'HTTP':
            return int(urllib.request.urlopen(url).info()['Content-Length'])
        elif endpoint == 'FTP':
            p = self._parse_ftp_url(url)
            ftp = self._get_ftp_connection(p["host"])
            return ftp.size(p["file_path"])
        elif endpoint == 'S3':
            k = self._s3_get_key(url)
            return k.size

    # Function to retrieve a particular set of bytes from the file.
    # Arguments:
    # res = network object created by get_url_obj()
    # endpoint = HTTP/FTP/S3
    # block_size = number of bytes to be considered a chunk to allow interrupts/resumes
    # start_pos = position to start at
    # max_range = maximum value to use for the range, same as the file's size
    # file = file handle to write out to
    def _get_buffer(self, res, endpoint, block_size, start_pos, max_range, file):
        if endpoint == "HTTP":
            return res.read(block_size)
        elif endpoint == "FTP":
            current_byte = start_pos

            # The Python ftplib requires transfer to pass to a callback function,
            # using this to break up the download into pieces. Unfortunately this
            # function by default accepts just the byte-block being pulled by
            # .retrbinary() so we need a nonlocal variable to help with printing
            # out the progress.
            def callback(data):
                nonlocal current_byte

                file.write(data)

                current_byte += len(data)
                self._generate_status_message("{0}  [{1:.2f}%]".format(current_byte, current_byte * 100 / max_range))

            res(callback, block_size, start_pos)

            return None
        elif endpoint == "S3":
            if start_pos >= max_range:
                return None # exit the while loop
            headers = {}

            # Offset by 1 since bytes are 0-based
            range_end = start_pos+block_size - 1

            headers['Range'] = 'bytes={0}-'.format(start_pos)

            if range_end <= max_range:
                headers['Range'] += "{0}".format(range_end)

            return res.get_contents_as_string(headers=headers)

    # Function to get the Key object from S3.
    # Arguments:
    # url = path to location of file on the web
    def _s3_get_key(self, url):
        self.logger.debug("In _s3_get_key.")

        url = url.lstrip('s3://')
        bucket_name = url.split('/', 1)[0]
        key = url.split('/', 1)[1]
        s3_conn = self._get_s3_connection()

        bucket = s3_conn.get_bucket(bucket_name)

        return bucket.get_key(key)

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

            md = get_instance_metadata(timeout=0.5,num_retries=1)

            if len(md.keys()) > 0:
                eps = ['S3','HTTP','FTP']
            else:
                eps = ['HTTP','FTP','S3'] # if none provided, use this order

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
        self.logger.debug("In checksum_matches. Checking {}.".format(file_path))
        md5 = hashlib.md5()

        # Read the file in chunks and build a final MD5
        with open(file_path, 'rb') as filehandle:
            for chunk in iter(lambda: filehandle.read(4096), b""):
                md5.update(chunk)

        valid = False
        if md5.hexdigest() == original_md5:
            valid = True

        self.logger.debug("Checksum valid? {}".format(valid))

        return valid

    # Function to output a status message to the user.
    # Argument:
    # message = the string to temporarily output to the user
    def _generate_status_message(self, message):
        status = message
        status = status + chr(8)*(len(status)+1) # backspace everything
        print("\r{0}".format(status),end="")
