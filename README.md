# Development VM

In order to facilitate testing and the creation of dev VMs, we
maintain an AWS VM image for quickly provisioning a VM with all the
build prereqs installed.  The AMI for the current image will be
[here](https://raw.githubusercontent.com/open-lambda/testing/master/dev/ami.txt).
The image can be used to create a t2.micro instance in the US-EAST-2
region.

## Creating a new AMI

The image is created with Vagrant and requires some extra plugins:

```
vagrant plugin install vagrant-aws
vagrant plugin install vagrant-aws-credentials
vagrant plugin install vagrant-ami
vagrant plugin install vagrant-reload
vagrant box add aws-dummy https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box
```

You can then build the image as follows:

```
cd dev
python build-ami.py
```

Note that this script requires AWS permissions as well github push
permissions for this repo.  The build takes about 10 minutes, and will
automatically update ami.txt and push it.
