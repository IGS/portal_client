# hmp_client

Python-based client for downloading data files hosted by the Human Microbiome Data Analysis and Coordination Center (hmpdacc.org). The client accepts as input a *manifest file* that lists the files to be downloaded. Manifest files can be generated using the shopping cart in the query interface at https://portal.hmpdacc.org.

## Running the client

There are 3 main ways to run the hmp_client:

1. Using a pre-built Chiron Docker image.
2. Using the Dockerfile in this repository.
3. Installing the dependencies manually.

### 1. Using a pre-built Chiron Docker image.

[Chiron](http://github.com/IGS/Chiron) is a collection of Dockerized tools and pipelines for metagenomics developed by the Human Microbiome Project members and originally used in the Microbiome Cloud Workshop held in Baltimore, Maryland in June of 2017. The hmp_client is installed in each of the Chiron Docker images. Using Chiron, the hmp_client Docker image, which contains the hmp_client and very little else, can be run like so:

```
$ git clone https://github.com/IGS/Chiron.git

$ cd Chiron

$ ./bin/hmp_client_interactive
```

This will download, build, and start the hmp_client Docker image and place you at a shell prompt inside the Docker container. From there the hmp_client program is available and can be run on a sample manifest file that's included in the image:

```
root@dba147a35981:/# hmp_client -manifest /opt/hmp_client/test/hmp_cart_example.tsv 
```

### 2. Using the Docker install in this repository

The client comes bundled with a Docker install that builds Python 3.6 as well as any dependencies specific to the client. One can use the Docker container to run the script using the following steps:

1. Invoke the Dockerfile to build. Change to the directory that contains the Dockerfile and then run this command:
```
  $ docker build . -t python_src
```
2. Now use the Docker image just built to create a container and run the client like so:
```
  $ docker run -it --rm --name run-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python_src bin/hmp_client -h
```

3. Test that it works by downloading a few small files to your current directory:
  * Basic functionality can be tested using the following example:
```
  $ docker run -it --rm --name run-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python_src bin/hmp_client --url=https://raw.githubusercontent.com/jmatsumura/hmp_client/master/test/hmp_cart_example.tsv
```
  * If running on EC2, this will automatically be detected and S3 will be the preferred endpoint. Example:
```
  $ docker run -it --rm --name run-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python_src bin/hmp_client --url=https://raw.githubusercontent.com/jmatsumura/hmp_client/master/test/hmp_cart_example.tsv
```
  * If you want to decide which endpoint to prioritize, you can pass it a single endpoint or a comma-separated list (e.g. 'HTTP' or 'HTTP,S3,FTP'). Example to override S3 prioritized endpoint on an EC2 instance:
```
  $ docker run -it --rm --name run-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python_src bin/hmp_client --url=https://raw.githubusercontent.com/jmatsumura/hmp_client/master/test/hmp_cart_example.tsv --endpoint_priority=HTTP
```
### 3. Installing the dependencies manually.

The hmp_client requires Python 3 and the Boto library:

- [Python 3.6](https://www.python.org/downloads/release/python-361/)

- [boto](https://pypi.python.org/pypi/boto) 

One easy way to install Python 3 and the necessary dependencies is to use Virtualenv.

## Using Aspera for FASP URLs

Aspera's fast file transfer technology can be used for some of the
files hosted by the iHMP DCC. The hmp_client does not yet directly
handle downloads from FASP endpoints/URLs, however these files may be
downloaded by using the Aspera *ascp* command-line utility, which can
be obtained from [the Aspera web site](http://downloads.asperasoft.com).

Another Python script in this repository, *manifest2ascp.py*, will
accept as input a manifest file and produce as output a shell script
that contains an ascp command for every FASP URL that it finds in the
manifest. That script is in the bin/ subdirectory of this repository:

[bin/manifest2ascp.py](bin/manifest2ascp.py)

It can be run with a command like the following after substituting in the appropriate username, password, Aspera executable path, Aspera options, and manifest file location:

```
$ ./manifest2ascp.py --manifest=hmp_cart_t2d_june_12_2017.tsv --user=username --password=password --ascp_path=/path/to/ascp/bin/ascp --ascp_options="-l 200M" > ascp-commands.sh
```

This should generate a shell script called “ascp-commands.sh” that you
can inspect and then run. By default it will download everything into
the current directory, but using the same directory structure that’s
present on the server. Some additional guidance on obtaining the ascp
executable and tuning its command-line options can be found here:

<https://www.hmpdacc.org/hmp/resources/download.php>
