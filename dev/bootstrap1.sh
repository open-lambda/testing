#!/usr/bin/env bash

set -x # echo commands
set -e # fast fail
export DEBIAN_FRONTEND=noninteractive

apt -y update
apt -y upgrade

locale-gen --purge en_US.UTF-8
echo -e 'LANG="en_US.UTF-8"\nLANGUAGE="en_US:en"\n' > /etc/default/locale
