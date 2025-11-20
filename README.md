# portal-client

A Python based client for downloading data files hosted by the Institute for
Genome Sciences (IGS). There are several portals running on the internet to
support various research efforts. Notably, the Neuroscience Multi-omic Archive
(NeMO, https://nemoarchive.org/) uses the portal to enable data exploration and
download. The client accepts a *manifest file* as an input. This file contains
URLs to the files to be downloaded. Manifest files can be generated using the
shopping cart functionality of the portal's query interface.

## Usage

When properly installed, portal-client will be available for direct invocation
from the command line. Running `which portal-client` should yield a result, and
will show precisely where the script is installed. General usage is available
by running `--help`, or `-h`.

```bash
$ portal-client --help
```

This will output all the options that portal-client supports as well as a 
brief explanation of what each option means and how it modifies the
execution.

## 1. Basic invocation

The following command is the most basic way of invoking the client. Simply by
specifying the path to a downloaded manifest file with the `-m`, or `--manifest`
option.

```bash
$ portal-client --manifest /path/to/my/manifest.tsv
```

Since manifests can list multiple URLs for an entry (a file can be obtained
from multiple sources), when using portal-client in this manner, it uses a
default set of protocols to download the data in the manifest. These
protocols are GS, S3, HTTP, FTP, and FASP. GCP uses the the Google Cloud SDK
to download files from Google Cloud Platform (GCP) buckets. HTTP uses the http
protocol for downloads of URLS starting with `http://` or `https://`, while
FTP uses the File Transfer Protocol for `ftp://` links, and S3 will fetch
data from Amazon AWS Simple Storage Service (S3) buckets. If a download
cannot be performed for a file with HTTP, and the file is available via S3
and FTP, by default, the client will attempt other protocols if the those URLs
are in the manifest...

## 2. Downloads from Google Cloud Platform (GCP)

The portal_client is able to retrieve data from Google Cloud Storage buckets.
Files in a google bucket, are addressable with URLs that begin with `gs://`,
so if a manifest includes such URLs, one must enable the GS
endpoint.

When accessing data from Google using this tool, Application Default Credentials
(ADC) are used instead of a client secrets file. ADC assumes that the Google
Cloud SDK (gcloud) is installed and that the user has already authenticated via
`gcloud auth login`. This authentication allows portal-client to access data in
Google Cloud Storage without requiring additional credential files. For the project
id, it is used internally by the SDK to associate API calls with a project for quota
tracking. It does not need to be the proejct that owns the bucket, but you must have
at least minimal access to that project (e.g., viewer role), otherwise the SDK may
throw a serviceusage error.

```bash
$ portal-client --manifest /path/to/my/manifest.tsv \
                --google-project-id <PROJECT ID> \
                --endpoint-priority GS,HTTP
```

## 3. Basic invocation on Amazon AWS

In the special case of executing portal-client on an EC2 instance on Amazon
AWS, it's faster and more economical to retrieve data from S3, since there
are no egress charges applied to such transfera. Therefore, the portal-client
is configured to automatically detect when it is invoked on AWS infrastructure
and moves the S3 protocol to the highest priority ahead of HTTP and FTP.

## 4. Altering the target directory

By default, portal_client will download data to the same directory (the
"working directory"), that the user invoked portal_client from. To alter the
location of where the data should be deposited, one must use the
`--destination` option:

```bash
$ portal-client --manifest /path/to/my/manifest.tsv \
                --destination /path/to/my/destination/directory
```

## 5. Overriding the default endpoint-priority

Sometimes, it may be advantageous to override the default endpoints, and their
priorities, that the portal_client will consider when downloading data. This is
accomplished with the `--endpoint-priority` option.

```bash
$ portal-client --manifest /path/to/my/manifest.tsv --endpoint-priority S3
```

In the above example, portal_client will NOT consider or attempt to download
data from HTTP or FTP urls. It will only use `s3://` urls. Any URLs that do NOT
use the `s3://` protocol will be skipped.

## 6. Downloads using Aspera

The portal_client includes support for downloading data via Aspera's
proprietary 'fasp' protocol. This is a proprietary high-performance protocol
that uses UDP packets. The `ascp` utility *must* be installed, and available,
on the same system as the portal client, or an error will occur. Please check
for the availablity of 'ascp' with `which`:

```bash
which ascp
```

One must also explicitly include 'FASP' in the endpoint priority listing. In
addition, the portal_client will also require the user to specify a username
with the `--user` option and will interactively prompt the user for their
Aspera server credential. The password will NOT be echoed to the
screen/terminal for security reasons. Example:

```bash
$ portal-client --manifest /path/to/my/manifest.tsv \
  --endpoint-priority FASP,HTTP \
  --user myusername
```

The above command will consider and download data from both `fasp://` and
`http://` urls, with preference given to Aspera.

Failure to specify the `--user` option will result in an error message when
'FASP' is used.

## 7. Disabling checksum validation

The portal_client usually verifies downloads after they happen by performing
and MD5 checksum on the downloaded data, and comparing it to the checksums
listed in the manifest file. However, if there is a mismatch, portal_client
will consider the download to be corrupted, or failed, and will exit out
with an error message. For very manifests that describe extremely large
datasets, the checksumming operation can be very time consuming.
To disable the checksum validation, simply pass an extra `--disable-validation`
Example:

```bash
$ portal-client --disable-validation --manifest /path/to/my/manifest.tsv
```

## 8. Debug mode

Users can see verbose additional information when executing portal-client by
passing the `--debug` option. This will typically result in a large amount of
output and can be used to trace where problems may be occuring.
