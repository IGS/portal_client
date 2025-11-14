<!-- markdownlint-disable MD033 -->
# Installation

There are several ways to install portal-client:

1. Using pip
2. Using VirtualEnv

The portal client requires Python 3, the Boto 3 library, and the Google
storage library:

- [Python 3.11](https://www.python.org/downloads/release/python-3110/)

- [boto3](https://pypi.python.org/pypi/boto3)

- [google-cloud-storage](https://pypi.org/project/google-cloud-storage/)

 
## Using pip

Another tool that is commonly used to install Python modules is pip. To use
pip to install portal-client, download the source code as shown above, then
invoke pip as root or using sudo:

  <pre>
  $ cd portal-client
  </pre>

  <pre>
  $ sudo pip3 install .
  </pre>

## Using VirtualEnv

An easy way to install portal-client and the necessary dependencies is to use
VirtualEnv and pip (or pip3 on some systems). The following commands assume you
already have VirtualEnv installed on your system and the portal-client software
downloaded.

1. Create a virtual environment

```bash
python3 -m venv /path/to/venvs/portal-client
```

2. Activate the virtual environment

```bash
source /path/to/venvs/portal-client/bin/activate
```

3. Install the portal-client into the virtual environment

```bash
pip3 install .
```

This will retrieve and install the dependencies as well.
