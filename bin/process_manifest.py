
# Contains the functions for downloading the contents of a manifest. 
#
# Author: James Matsumura
# Contact: jmatsumura@som.umaryland.edu

# base 3.6 lib(s)
import urllib,hashlib,os,shutil,sys
# additional dependencies (get from pip) 
import boto
from boto.utils import get_instance_metadata

# Function to download each URL from the manifest.
# Arguments:
# manifest = manifest dict data structure created by functions in convert_to_manifest.py
# destination = set destination to place output declared when calling client.py
# priorities = endpoint priorities established by get_prioritized_endpoint
def download_manifest(manifest,destination,priorities):
    
    # iterate over the manifest data structure, one ID/file at a time
    for key in manifest: 

        url = get_prioritized_endpoint(manifest[key]['urls'],priorities)

        # Handle private data or simply nodes that are not correct and lack 
        # endpoint data
        if url == "":
            print("No valid URL found for file ID: {0}".format(manifest[key]['id']))
            continue

        file_name = "{0}/{1}".format(destination,url.split('/')[-1])

        if not os.path.exists(file_name): # only need to download if the file is not present

            # Handle S3 connections if the endpoint is preferred
            s3_conn = ""
            if url.lower().startswith('s3'):
                s3_conn = boto.connect_s3(anon=True)
                url = url.lstrip('s3://')

            tmp_file_name = "{0}.partial".format(file_name)

            # If we only have part of a file, get the new start position
            current_byte = 0

            if os.path.exists(tmp_file_name):
                current_byte = os.path.getsize(tmp_file_name)

            headers = {}
            headers['Range'] = 'bytes={0}-'.format(current_byte)
            
            res = get_url_obj(url,s3_conn,headers)
            
            with open(tmp_file_name,'ab') as file:

                # Need to pull the size without the potential bytes buffer
                file_size = get_file_size(url,s3_conn)
                print("Downloading file: {0} Bytes: {1}".format(file_name, file_size))

                block_sz = 8192

                while True:

                    buffer = res.read(block_sz)

                    if not buffer:
                        break

                    file.write(buffer)

                    current_byte += len(buffer)

                    status = "{0}  [{1:.2f}%]".format(current_byte, current_byte * 100 / file_size)
                    status = status + chr(8)*(len(status)+1)
                    print("\r{0}".format(status),end="")

            # If the download is complete, establish the final file
            if checksum_matches(tmp_file_name,manifest[key]['md5']):
                shutil.move(tmp_file_name,file_name)
            else:
                print("\rMD5 check failed for the file: {0}.".format(url.split('/')[-1]))

# Function to get a network object of the file that can be iterated over.
# Arguments:
# url = path to location of file on the web
# s3_conn = connection to S3 if this is an S3 endpoint
# header = range to pull from the file
def get_url_obj(url,s3_conn,header):
    if not s3_conn:
        req = urllib.request.Request(url,headers=header)
        try:
            return urllib.request.urlopen(req)
        except:
            sys.exit("Error -- cannot get network object for URL: {0}".format(url))
    else:
        k = s3_get_key(url,s3_conn)
        try:
            return k.open()
        except:
            sys.exit("Error -- cannot get network object for URL: {0}".format(url))
            

# Function to retrieve the file size from either an S3 or non-S3 endpoint.
# Arguments:
# url = path to location of file on the web
# s3_conn = connection to S3 if this is an S3 endpoint
def get_file_size(url,s3_conn):
    if not s3_conn:
        return int(urllib.request.urlopen(url).info()['Content-Length'])
    else:
        k = s3_get_key(url,s3_conn)
        return k.size 

# Function to get the Key object from S3.
# Arguments:
# url = path to location of file on the web
# s3_conn = connection to S3 if this is an S3 endpoint
def s3_get_key(url,s3_conn):
    bucket = url.split('/',1)[0]
    key = url.split('/',1)[1]
    b = s3_conn.get_bucket(bucket)
    return b.get_key("/{0}".format(key))

# Function to get the URL for the prioritized endpoint that the user requests.
# Note that priorities can be a list of ordered priorities.
# Arguments:
# manifest_urls = the CSV set of endpoint URLs
# priorities = priorities declared when calling client.py
def get_prioritized_endpoint(manifest_urls,priorities):

    chosen_url = ""

    urls = manifest_urls.split(',')
    eps = priorities.split(',')

    # If the user didn't provide a set of priorities, then prioritize based on
    # whether on an EC2 instance.
    if eps[0] == "":

        md = get_instance_metadata(timeout=0.5,num_retries=1)

        if len(md.keys()) > 0:
            eps = ['S3','HTTP','FTP','FASP']
        else:
            eps = ['HTTP','FTP','S3','FASP'] # if none provided, use this order

    # Priorities are entered with highest first, so simply check until we find
    # a valid endpoint and then leave.
    for ep in eps:
        if chosen_url != "":
            break
        else:
            for url in urls:
                if url.startswith(ep.lower()):
                    chosen_url = url

    return chosen_url

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
