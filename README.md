# hmp_client

Python-based client for downloading files hosted by the Human Microbiome Data Analysis and Coordination Center (hmpdacc.org).

This comes bundled with a Docker install that builds Python 2.7 as well as any dependencies specific to the client. One can use the Docker container to run the script using the following steps:

1. Invoke the Dockerfile to build. For example, if you are in the directory where the Dockerfile is run the command:
  * `docker build . -t python_src`
2. Now use the Docker image just built to create a container and run the client like so:
  * `docker run -it --rm --name run-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python_src python client.py -help`
    * NOTE: this run command cleans up after itself, so you should not see any containers Python containers lingering.

## Dependencies:
- [Python 2.7](https://www.python.org/download/releases/2.7/)
- [boto](https://pypi.python.org/pypi/boto) 
