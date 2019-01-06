#!/usr/bin/env python3
import os, sys, time, datetime, boto3
from subprocess import check_call, check_output
from os.path import expanduser

s3 = boto3.client("s3")


def run(cmd):
    check_call(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)


def aws_log():
    with open("/var/log/cloud-init-output.log") as f:
        return f.read()


def s3_put(key, value):
    r = s3.put_object(Bucket='open-lambda-public',
                      Key=key,
                      Body=value.encode('utf-8'),
                      ContentType='text/plain')


def main():
    now = datetime.datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    dirname = 'vm/%s' % now

    # upload AWS log to S3
    s3_put(dirname+'/cloud-init-output.log', aws_log())

    os.chdir(expanduser("~"))
    run('git clone https://github.com/open-lambda/open-lambda.git')
    os.chdir(expanduser("open-lambda"))
    run('make')
    try:
        with open("tests.out", "w") as f:
            check_call("make test-all", shell=True, stdout=f, stderr=f)
        result = 'PASS'
    except:
        result = 'FAIL'

    # upload test results to S3
    s3_put(dirname+'/test.txt', result)
    with open('tests.out') as f:
        s3_put(dirname+'/tests.out', f.read())

    # kill the VM (it has been configured to terminate on shutdown)
    run('poweroff -f')


if __name__ == '__main__':
    main()
