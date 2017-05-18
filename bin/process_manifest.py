
# Contains the functions for downloading the contents of a manifest. 
#
# Author: James Matsumura
# Contact: jmatsumura@som.umaryland.edu

# base 3.6 lib(s)
import urllib,hashlib,os,shutil,sys
from ftplib import FTP
# additional dependencies (get from pip) 
import boto
from boto.utils import get_instance_metadata

# Establish a S3 connection.
s3_conn = boto.connect_s3(anon=True)

# Establish a FTP connection.
ftp = FTP('public-ftp.hmpdacc.org')
ftp.login('client') # any PW works as it's public

# Function to download each URL from the manifest.
# Arguments:
# manifest = manifest dict data structure created by functions in convert_to_manifest.py
# destination = set destination to place output declared when calling client.py
# priorities = endpoint priorities established by get_prioritized_endpoint
# block_sz = the byte size to break the file into to allow for interrupted downloads
def download_manifest(manifest,destination,priorities,block_sz):
    
    # build a list of elements to indicate how many and why the files failed
    # 1 = no valid URL in manifest
    # 2 = URL exists, but not accessible at the location specified
    # 3 = MD5 check failed for file (file is corrupted or the wrong MD5 is attached to the file)
    failed_files = [] 

    # iterate over the manifest data structure, one ID/file at a time
    for key in manifest: 

        url_list = get_prioritized_endpoint(manifest[key]['urls'],priorities)

        # Handle private data or simply nodes that are not correct and lack 
        # endpoint data
        if not url_list:
            print("No valid URL found in the manifest for file ID {0}".format(key))
            failed_files.append(1)
            continue

        file_name = "{0}/{1}".format(destination,url_list[0].split('/')[-1])

        if not os.path.exists(file_name): # only need to download if the file is not present

            tmp_file_name = "{0}.partial".format(file_name)

            # If we only have part of a file, get the new start position
            current_byte = 0
            if os.path.exists(tmp_file_name):
                current_byte = os.path.getsize(tmp_file_name)

            # Need to try get the others to work like this, but for now HTTP 
            # is the only one that can pull bytes in chunks without needing to
            # drop the connection.
            http_header = {} 
            http_header['Range'] = 'bytes={0}-'.format(current_byte)
            
            res,endpoint = ("" for i in range(2))
            eps = []

            for url in url_list:
                endpoint = url.split(':')[0].upper()
                eps.append(endpoint)
                res = get_url_obj(url,endpoint,http_header)

                if res != "error": # if we get back a network object, continue
                    break

            if res == "error": # if all attempts resulted in no object, move on to next file
                print("skipping file ID {0} as none of the URLs checked {1} yielded a valid file".format(key,eps))
                failed_files.append(2)
                continue

            with open(tmp_file_name,'ab') as file:

                # Need to pull the size without the potential bytes buffer
                file_size = get_file_size(url,endpoint)
                print("downloading file (via {0}): {1} | total bytes = {2}".format(endpoint, file_name, file_size))

                while True:

                    if block_sz > file_size:
                        generate_status_message("block size greater than total file size, pulling entire file in one go")

                    buffer = get_buffer(res,endpoint,block_sz,current_byte,file_size,file)
                    
                    if not buffer: # note that only HTTP/S3 make it beyond this point
                        break

                    file.write(buffer)

                    current_byte += len(buffer)
                    generate_status_message("{0}  [{1:.2f}%]".format(current_byte, current_byte * 100 / file_size))

            # If the download is complete, establish the final file
            if checksum_matches(tmp_file_name,manifest[key]['md5']):
                shutil.move(tmp_file_name,file_name)
                failed_files.append(0)
            else:
                print("\rMD5 check failed for the file ID {0} , data may be corrupted".format(key))
                failed_files.append(3)

        else: # file already done downloading
            failed_files.append(0)

    return failed_files

# Function to get a network object of the file that can be iterated over.
# Arguments:
# url = path to location of file on the web
# endpoint = HTTP/FTP/S3
# http_header = HTTP range to pull from the file, the other endpoints require 
# this processing in the get_buffer() function.
def get_url_obj(url,endpoint,http_header):
    if endpoint == "HTTP":
        res = ""

        try:
            req = urllib.request.Request(url,headers=http_header)
            res = urllib.request.urlopen(req)
        except:
            res = ""

        if res:
            return res

    if endpoint == "FTP":
        ftp_loc = url.split('public-ftp.hmpdacc.org')[1]
        if list(ftp.mlsd(ftp_loc)): # make sure there's something there
            return url.split('public-ftp.hmpdacc.org')[1]

    elif endpoint == "S3":
        res = s3_get_key(url)
        if res:
            return res

    # If made it here, no network object established
    return "error"
            
# Function to retrieve the file size.
# Arguments:
# url = path to location of file on the web
# endpoint = HTTP/FTP/S3
def get_file_size(url,endpoint):
    if endpoint == 'HTTP':
        return int(urllib.request.urlopen(url).info()['Content-Length'])

    elif endpoint == 'FTP':
        return ftp.size(url.split('public-ftp.hmpdacc.org')[1])

    elif endpoint == 'S3':
        k = s3_get_key(url)
        return k.size 

# Function to retrieve a particular set of bytes from the file.
# Arguments:
# res = network object created by get_url_obj()
# endpoint = HTTP/FTP/S3
# block_sz = number of bytes to be considered a chunk to allow interrupts/resumes
# start_pos = position to start at
# max_range = maximum value to use for the range, same as the file's size
# file = file handle to write out to
def get_buffer(res,endpoint,block_sz,start_pos,max_range,file):
    if endpoint == "HTTP":
        return res.read(block_sz)

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
            generate_status_message("{0}  [{1:.2f}%]".format(current_byte, current_byte * 100 / max_range))

        ftp.retrbinary("RETR {0}".format(res),callback,blocksize=block_sz,rest=start_pos)

        return None

    elif endpoint == "S3":
        if start_pos >= max_range:
            return None # exit the while loop
        headers = {}
        range_end = start_pos+block_sz-1 # offset by 1 since bytes are 0-based
        headers['Range'] = 'bytes={0}-'.format(start_pos)
        if range_end <= max_range:
            headers['Range'] += "{0}".format(range_end)
        return res.get_contents_as_string(headers=headers)

# Function to get the Key object from S3.
# Arguments:
# url = path to location of file on the web
def s3_get_key(url):
    url = url.lstrip('s3://')
    bucket = url.split('/',1)[0]
    key = url.split('/',1)[1]
    b = s3_conn.get_bucket(bucket)
    return b.get_key(key)

# Function to get the URL for the prioritized endpoint that the user requests.
# Note that priorities can be a list of ordered priorities.
# Arguments:
# manifest_urls = the CSV set of endpoint URLs
# priorities = priorities declared when calling client.py
def get_prioritized_endpoint(manifest_urls,priorities):

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

                # Quick fix until the correct endpoints for the demo data (bucket+key) are established on S3. 
                if 's3://' in url and 'HMDEMO' in url:
                    elements = url.split('/')
                    url = "s3://{0}/DEMO/{1}/{2}".format(elements[2],elements[4],"/".join(elements[-4:]))

                url_list.append(url)

    return url_list

# This function failing is largely telling that the data in OSDF for the
# particular file's MD5 is not correct.
# Arguments:
# file_path = location of the file just downloaded which requires an integrity check
# original_md5 = MD5 provided by OSDF data
def checksum_matches(file_path,original_md5):

    md5 = hashlib.md5()

    # Read the file in chunks and build a final MD5
    with open(file_path,'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)

    if md5.hexdigest() == original_md5:
        return True
    else:
        return False

# Function to output a status message to the user.
# Argument:
# message = the string to temporarily output to the user
def generate_status_message(message):
    status = message
    status = status + chr(8)*(len(status)+1) # backspace everything
    print("\r{0}".format(status),end="")
