# Testing and Development

## Test Summary

Daily OpenLambda tests will be uploaded here:

[https://s3.us-east-2.amazonaws.com/open-lambda-public/tests.html](https://s3.us-east-2.amazonaws.com/open-lambda-public/tests.html)

## Development VM

In order to facilitate testing and the creation of dev VMs, we
maintain an AWS VM image for quickly provisioning a VM with all the
build prereqs installed.  The AMI for the current image will be
[here](https://raw.githubusercontent.com/open-lambda/testing/master/dev-build/ami.txt).
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
cd dev-build
python build-ami.py
```

Note that this script requires AWS permissions as well github push
permissions for this repo.  The build takes about 10 minutes, and will
automatically update ami.txt and push it.

## Spinning Up a Dev VM

You'll need the same vagrant plugins mentioned in the above section.
Then do the following:

```
cd dev-deploy
vagrant up
vagrant ssh
```

The pull, build, and test:

```
sudo su
git clone https://github.com/open-lambda/open-lambda.git
cd open-lambda
make
make test
```

## Lambda Config

The code for the lambda that launches the EC2 test VM is located at
`lambdas/launch-ec2.py`.  The new VM will run the code in
`tests/ec2-test.py`.

Upload `launch-ec2.py` as a new lambda function, with whatever
triggers are appropriate.  The entry function is main.

You'll need to do some permission config for the lambda:
* give the lambda has permission to launch EC2 instances
* give the lambda has permission to pass a role to new EC2 instances so they can write to S3

The lambda uses the `requests` module, which is not deployed with
Python.  You'll need to create a lambda layer with this installed.
You can do so with the following steps:

```
python3 -m venv lambda-base
source ./lambda-base/bin/activate
pip install requests
aws lambda publish-layer-version --layer-name lambda-base --zip-file fileb://lambda-base.zip 
```

Configure the function to use this layer, and add
`PYTHONPATH=/opt/lib/python3.6/site-packages` to the environment
variables for the function.
