# Basic Python3.6 install
FROM ubuntu:18.04

RUN apt-get -y update && apt-get install -y python3.6 python3-pip

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN pip3 install boto

CMD ["python3"]
