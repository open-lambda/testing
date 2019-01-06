#!/usr/bin/env bash

set -x # echo commands
set -e # fast fail
export DEBIAN_FRONTEND=noninteractive

# ubuntu
apt -y install linux-image-extra-$(uname -r)
apt -y install linux-image-extra-virtual
apt -y install golang
apt -y install curl
apt -y install git
apt -y install docker.io
apt -y install cgroup-tools cgroup-bin
apt -y install python2.7-dev
apt -y install python-pip
apt -y install python3-pip
service docker restart

# python
pip install netifaces
pip install rethinkdb
pip install tornado
pip3 install boto3

# go
wget -q -O /tmp/go1.7.6.tar.gz https://storage.googleapis.com/golang/go1.7.6.linux-amd64.tar.gz
tar -C /usr/local -xzf /tmp/go1.7.6.tar.gz
mv /usr/bin/go /usr/bin/go-old
ln -s /usr/local/go/bin/go /usr/bin/go
