<!-- markdownlint-disable MD033 -->
# Installation

There are several ways to install portal_client:

1. Using easy_install
2. Using pip
3. Using VirtualEnv
4. Using Docker

The portal client requires Python 3, the Boto library, and two Google
python libraries:

- [Python 3.6](https://www.python.org/downloads/release/python-361/)

- [boto](https://pypi.python.org/pypi/boto)

- [google-auth-oauthlib](https://pypi.org/project/google-auth-oauthlib/)

- [google-cloud-storage](https://pypi.org/project/google-cloud-storage/)

## Using easy_install

Download or clone the portal_client code from github.

  <pre>
  $ cd portal_client
  </pre>

Then one can simply use easy_install. If you have root privileges:

  <pre>
  # easy_install .
  </pre>

or with sudo:

  <pre>
  $ sudo easy_install .
  </pre>

If you are performing a non-root installation, you can still use
easy_install. First, pick an installation directory. In this example we'll
use /tmp. Then add the installation directory to your PYTHONPATH environment
variable if it isn't already there:

  <pre>
  $ export PYTHONPATH=$PYTHONPATH:/tmp
  </pre>

Then invoke easy_install with the --install-dir option. Note the final '.',
which tells easy_install where to look for the setup.py script.

  <pre>
  $ easy_install --install-dir /tmp .
  </pre>
  
## Using pip

Another tool that is commonly used to install Python modules is pip. To use
pip to install portal_client, download the source code as shown above, then
invoke pip as root or using sudo:

  <pre>
  $ cd portal_client
  </pre>

  <pre>
  $ sudo pip3 install .
  </pre>

## Using VirtualEnv

An easy way to install portal_client and the necessary dependencies is to use
VirtualEnv and pip (or pip3 on some systems). The following commands assume you
already have VirtualEnv installed on your system and the portal_client software
downloaded.

1. Create a virtual environment

```bash
virtualenv /path/to/venvs/portal_client
```

2. Activate the virtual environment

```bash
source /path/to/venvs/portal_client/bin/activate
```

3. Install the portal_client into the virtual environment

Switch back to your download of portal_client and execute pip3 install as
follows:

```bash
pip3 install .
```

This will retrieve and install the dependencies as well.

## Using Docker

The portal_client code comes with a Dockerfile, which, when used, will
build a docker image with Python 3.6 as well as the dependencies specific to
the portal client. One can then use this Docker image to execute the client
using the following steps:

1. Build the image. Change to the directory containing the Dockerfile and execute:

```bash
docker build -t portal_client .
```

2. Use the built image to start a container and execute the client:

```bash
docker run -ti --rm portal_client portal_client --help
```

3. Test the container by downloading a few small files. The command below should
download two files to your current directory ($PWD). This works because we have
mapped your current working directory to the /tmp directory in the container with
the -v option, and we are executing the client in the /tmp directory with the use
of the -w option.

```bash
docker run -v "$PWD:/tmp" -w /tmp -ti --rm portal_client portal_client \
    --url=https://raw.githubusercontent.com/IGS/portal_client/master/example_manifests/example_manifest.tsv
```

  * If running on EC2, this will automatically be detected and S3 will be the preferred endpoint. Example:

```bash
docker run -ti --rm -v "$PWD":/tmp -w /tmp portal_client portal_client \
    --url=https://raw.githubusercontent.com/IGS/portal_client/master/example_manifests/example_manifest.tsv
```

  * If you wish to control which protocol/endpoint to prioritize, you can pass
a single endpoint or a comma-separated list (e.g. 'HTTP' or 'HTTP,S3,FTP').
For example, to override the S3 prioritized endpoint on an AWS EC2 instance with
the HTTP endpoint:

```bash
docker run -ti --rm -v "$PWD:/tmp" -w /tmp portal_client portal_client \
     --endpoint-priority=HTTP \
    --url=https://raw.githubusercontent.com/IGS/portal_client/master/example_manifests/example_manifest.tsv
```
