#!/usr/bin/env bash

set -x # echo commands
set -e # fast fail
export DEBIAN_FRONTEND=noninteractive

# ubuntu
apt -y install linux-modules-extra-$(uname -r)
apt -y install linux-image-extra-virtual
apt -y install curl git docker.io cgroup-tools cgroup-bin emacs24-nox htop sysstat
apt -y install python2.7-dev python-pip python3-pip
service docker restart

# python (2+3)
pip install netifaces
pip install rethinkdb
pip install tornado
pip3 install boto3

# go 1.12.5
wget -q -O /tmp/go1.12.5.linux-amd64.tar.gz https://dl.google.com/go/go1.12.5.linux-amd64.tar.gz
tar -C /usr/local -xzf /tmp/go1.12.5.linux-amd64.tar.gz
ln -s /usr/local/go/bin/go /usr/bin/go

# disable auto updates
sudo apt-get -y remove unattended-upgrades
