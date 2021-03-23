# portal_client

Python-based client for downloading data files hosted by the an instance of
the portal software developed by the GDC and further modified by the
Institute for Genome Sciences (IGS). There are several portals running on the
internet to support various research efforts. Notably, the Human Microbiome
Project Data Analysis and Coordination Center (hmpdacc.org) uses the portal
to enable data exploration and download. The client accepts a *manifest file*
as an input. This file contains URLs to the files to be downloaded. Manifest
files can be generated using the shopping cart functionality of the portal's
query interface.

## Usage

When properly installed, portal_client will be available for direct invocation
from the command line. Running `which portal_client` should yield a result, and
will show precisely where the script is installed. General usage is available
by simply using the well-known `--help`, or `-h`.

```bash
portal_client --help
```

This will output all the options that portal_client supports as well as a
very brief explanation of what each option means and how it modifies the
execution.

## 1. Basic invocation

The following command is the most basic way of invoking the client. Simply by
specifying the path to a downloaded manifest file with the `-m`, or `--manifest`
option.

```bash
portal_client --manifest /path/to/my/manifest.tsv
```

Since manifests can list multiple URLs for an entry (a file can be obtained
from multiple sources), when using portal_client in this manner, it uses a
default set of protocols to download the data in the manifest. These
protocols are, in priority order: HTTP, FTP, and S3. HTTP uses the http
protocol for downloads of URLS starting with `http://` or `https://`, while
FTP uses the File Transfer Protocol for `ftp://` links, and S3 will fetch
data from Amazon AWS Simple Storage Service (S3) buckets. If a download
cannot be performed for a file with HTTP, and the file is available via S3
and FTP, by default, the client will next attempt an FTP transfer, followed
finally by S3...

## 2. Basic invocation on Amazon AWS

In the special case of executing portal_client on an EC2 instance on Amazon
AWS, it's faster and more economical to retrieve data from S3, since there
are no egress charges applied to such transfer. Therefore, the portal_client
is configured to automatically detect when it is invoked on Amazon infrastructure
and move the S3 protocol to the highest priority ahead of HTTP and FTP. The
endpoint priority when running on EC2 is therefore: S3, HTTP, FTP, as opposed
to the normal priority of HTTP, FTP, S3.

## 3. Altering the target directory

By default, portal_client will download data to the same directory (the
"working director"), that the user invoked portal_client from. To alter the
location of where the data should be deposited, one must use the
`--destination` option:

first be generated. Documentation for how that is accomplished is available
from Google and is beyond the scope of this guide, but it is used to
authorize the portal_client to access data in a Google storage bucket.
Additionally, the ID of a valid Google project must also be specified with
the `--google-project-id` option. A full example is below:

```bash
portal_client --manifest /path/to/my/manifest.tsv \
  --destination /path/to/my/destination/directory
```

## 4. Overriding the default endpoint-priority

Sometimes, it may be advantageous to override the default endpoints, and their
priorities, that the portal_client will consider when downloading data. This is
accomplished with the `--endpoint-priority` option.

```bash
portal_client --manifest /path/to/my/manifest.tsv --endpoint-priority S3
```

In the above example, portal_client will NOT consider or attempt to download
data from HTTP or FTP urls. It will only use `s3://` urls. Any URLs that do NOT
use the `s3://` protocol will be skipped.

## 5. Downloads using Aspera

The portal_client includes support for downloading data via Aspera's
propietary 'fasp' protocol. This is a proprietary high-performance protocol
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
portal_client --manifest /path/to/my/manifest.tsv \
  --endpoint-priority FASP,HTTP \
  --user myusername
```

The above command will consider and download data from both `fasp://` and
`http://` urls, with preference given to Aspera.

Failure to specify the `--user` option will result in an error message when
'FASP' is used.

## 6. Downloads from Google Cloud Platform (GCP)

The portal_client is able to retrieve data from Google Cloud Storage buckets.
Files in a google bucket, are addressable with URLs that begin with `gs://`,
so if a manifest includes such URLs, one must enable the GS
endpoint.

When accessing data in this manner from Google, a "client secrets" file must
first be generated. Documentation for how that is accomplished is available
from Google and is beyond the scope of this guide, but it is used to
authorize the portal_client to access data in a Google storage bucket.
Specify the path to the client secrets file with the
`--google-client-secrets` option. Additionally, the ID of a valid Google
project must also be specified with the `--google-project-id` option. A full
example is below:

```bash
portal_client --manifest /path/to/my/manifest.tsv \
  --endpoint-priority GS,HTTP \
  --google-client-secrets /path/to/my/client-secrets.json \
  --google-project-id my-google-project-id
```

## 7. Disabling checksum validation

The portal_client usually verifies downloads after they happen by performing
and MD5 checksum on the downloaded data, and comparing it to the checksums
listed in the manifest file. However, if there is a mismatch, portal_client
will consider the download to be corrupted, or failed, and will exit out
with an error message. For very manifests that describe extremely large
datasets, the checksumming operation can be very costly, or time consuming.
To disable the checksum validation, simply pass an extra `--disable-validation`
Example:

```bash
portal_client --disable-validation --manifest /path/to/my/manifest.tsv
```

## 8. Debug mode

Users can see verbose additional information when executing portal_client by
passing the `--debug` option. This will typically result in a large amount of
output and can be used to trace where problems may be occuring. This output is
frequently used by developers when troubleshooting.
