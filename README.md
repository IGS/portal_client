# hmp_client

Python-based client for downloading data files hosted by the Human Microbiome Data Analysis and Coordination Center (hmpdacc.org and ihmpdcc.org). The client accepts as input a *manifest file* that lists the files to be downloaded. Manifest files can be generated using the shopping cart in the query interface at http://portal.ihmpdcc.org.

## Running the client

There are 3 main ways to run the hmp_client:

1. Using a pre-built Chiron Docker image.
2. Using the Dockerfile in this repository.
3. Installing the dependencies manually.

### Using a pre-built Chiron Docker image.

[Chiron](http://github.com/IGS/Chiron) is a collection of Dockerized tools and pipelines for metagenomics developed by the Human Microbiome Project members and was initially developed for the Microbiome Cloud Workshop, held in June 2017 in Baltimore, Maryland. The hmp_client is installed in each of the Chiron Docker images. Using Chiron, the hmp_client Docker image, which contains the hmp_client and very little else, can be run like so:

```
git clone https://github.com/IGS/Chiron.git
cd Chiron
./bin/hmp_client_interactive
```

This will download, build, and start the hmp_client Docker image and place you at a shell prompt inside the Docker image. From there the hmp_client program is available and can be run on a sample manifest file that's included in the image:

```
root@dba147a35981:/# hmp_client -manifest /opt/hmp_client/hmp_client-1.1/test/hmp_cart_example.tsv 
```

### Using the Docker install in this repository

The client comes bundled with a Docker install that builds Python 3.6 as well as any dependencies specific to the client. One can use the Docker container to run the script using the following steps:

1. Invoke the Dockerfile to build. Change to the directory that contains the Dockerfile and then run this command:
  * `docker build . -t python_src`
2. Now use the Docker image just built to create a container and run the client like so:
  * `docker run -it --rm --name run-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python_src python3 client.py -h`
    * NOTE: this run command cleans up after itself, so you should not see any Python containers lingering (although images will remain unless you remove them).
3. Test that it works by downloading a few small files to your current directory:
  * Basic functionality can be tested using the following example:
    * `docker run -it --rm --name run-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python_src python3 client.py -url https://raw.githubusercontent.com/jmatsumura/hmp_client/master/test/hmp_cart_example.tsv`
  * If running on EC2, this will automatically be detected and S3 will be the preferred endpoint. Example:
    * `docker run -it --rm --name run-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python_src python3 client.py -url https://raw.githubusercontent.com/jmatsumura/hmp_client/master/test/hmp_cart_example.tsv`
  * If you want to decide which endpoint to prioritize, you can pass it a single endpoint or a comma-separated list (e.g. 'HTTP' or 'HTTP,S3,FTP'). Example to override S3 prioritized endpoint on an EC2 instance:
    * `docker run -it --rm --name run-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python_src python3 client.py -url https://raw.githubusercontent.com/jmatsumura/hmp_client/master/test/hmp_cart_example.tsv -endpoint_priority HTTP`

### Installing the dependencies manually.

The hmp client requires Python 3 and the Boto library:

- [Python 3.6](https://www.python.org/download/releases/2.7/)
- [boto](https://pypi.python.org/pypi/boto) 

## Manifest Format

If generating your own manifest file, you **must** follow the same formatting as the following: 
* Requires tab-separated values (TSV) in the following structure with a header line included and the same order for the data as seen here.

|id|md5|size|urls|
|---|---|---|---|
|8d65351c0cb6f7eb9726a1c463f1c34e|626b3b87b8958e1db84489d727d16607|2353731|http:blahblah,ftp:blashblah,s3:blahblah|
|08c2ad843ddce68446571cfc0f4e7b19|87256429a37cf57c044879f974cd7421|2386996|http:blahblah,ftp:blahblah,s3:blahblah|

## Using Aspera for FASP URLs

Aspera's FASP technology can be used for some of the files hosted by the iHMP DCC. This client does not handle downloads from FASP endpoints. Please follow the tutorial found [here](http://ihmpdcc.org/resources/aspera.php) if you wish to download using FASP.
