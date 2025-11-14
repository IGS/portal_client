FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && apt-get install -y curl lsb-release gnupg git python3.12 python3-pip python3-boto3 python3-requests python3-venv

# Add the Google Cloud SDK APT repository
RUN curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
        > /etc/apt/sources.list.d/google-cloud-sdk.list

# Create keyring and import key (modern, preferred method)
RUN curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
      | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

RUN mkdir /root/portal-client
COPY lib /root/portal-client/lib/
COPY portal-client pyproject.toml /root/portal-client/
COPY DESC CHANGES /root/portal-client/

RUN python3 -m venv /root/portal-client-venv && \
    cd /root/portal-client && \
    /root/portal-client-venv/bin/pip3 install .
