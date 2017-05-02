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

## Manifest Format
If generating your own manifest, you **must** follow the same formatting as the following: 
* Requires tab-separated values (TSV) in the following structure with a header line included and the same order for the data as seen here.
|id|md5|size|urls|
|8d65351c0cb6f7eb9726a1c463f1c34e|626b3b87b8958e1db84489d727d16607|2353731|http://downloads.hmpdacc.org/data/HM16STR/HMDEMO/SRP002429/stool/not_affected/SRS066784.fsa,ftp://public-ftp.hmpdacc.org/HM16STR/HMDEMO/SRP002429/stool/not_affected/SRS066784.fsa,s3://human-microbiome-project/HHS/HM16STR/HMDEMO/SRP002429/stool/not_affected/SRS066784.fsa|
|08c2ad843ddce68446571cfc0f4e7b19|87256429a37cf57c044879f974cd7421|2386996|http://downloads.hmpdacc.org/data/HMR16S/HMDEMO/SRP002429/SRR043474.sff.bz2,ftp://public-ftp.hmpdacc.org/HMR16S/HMDEMO/SRP002429/SRR043474.sff.bz2,s3://human-microbiome-project/HHS/HMR16S/HMDEMO/SRP002429/SRR043474.sff.bz2|
