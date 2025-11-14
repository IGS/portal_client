## Using Docker

The portal-client code comes with a Dockerfile, which, when used, will
build a docker image with Python 3.12 as well as the dependencies specific to
the portal client. One can then use this Docker image to execute the client
using the following steps:

1. Build the image. Change to the directory containing the Dockerfile and execute:

```bash
docker build -t portal-client .
```

2. Use the built image to start a container and execute the client:

```bash
docker run -ti --rm portal-client portal-client --help
```

3. Test the container by downloading a few small files. The command below should
download two files to your current directory ($PWD). This works because we have
mapped your current working directory to the /tmp directory in the container with
the -v option, and we are executing the client in the /tmp directory with the use
of the -w option.

```bash
docker run -v "$PWD:/tmp" -w /tmp -ti --rm portal-client portal-client \
    --url=https://raw.githubusercontent.com/IGS/portal_client/master/example_manifests/example_manifest.tsv
```

  * If running on EC2, this will automatically be detected and S3 will be the preferred endpoint. Example:

```bash
docker run -ti --rm -v "$PWD":/tmp -w /tmp portal-client portal-client \
    --url=https://raw.githubusercontent.com/IGS/portal_client/master/example_manifests/example_manifest.tsv
```

  * If you wish to control which protocol/endpoint to prioritize, you can pass
a single endpoint or a comma-separated list (e.g. 'HTTP' or 'HTTP,S3,FTP').
For example, to override the S3 prioritized endpoint on an AWS EC2 instance with
the HTTP endpoint:

```bash
docker run -ti --rm -v "$PWD:/tmp" -w /tmp portal-client portal-client \
    --endpoint-priority=HTTP \
    --url=https://raw.githubusercontent.com/IGS/portal_client/master/example_manifests/example_manifest.tsv
```
