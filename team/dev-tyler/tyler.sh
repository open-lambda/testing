#!/usr/bin/env bash

set -x # echo commands
set -e # fast fail
export DEBIAN_FRONTEND=noninteractive

apt -y install emacs-nox

git config --global user.name "Tyler Caraza-Harter"
git config --global user.email tylerharter@gmail.com

cd ~
git clone https://github.com/tylerharter/tools.git

cp ~/tools/.emacs ~/.emacs
sed -i -e 's/git_co\///g' ~/.emacs

cd ~
git clone https://github.com/open-lambda/open-lambda.git
cd open-lambda
make
