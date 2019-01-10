#!/usr/bin/env python3
import os, sys, time, datetime, boto3
from subprocess import check_call, check_output
from os.path import expanduser

BUCKET = 'open-lambda-public'
URL = 'https://s3.us-east-2.amazonaws.com/open-lambda-public/'
s3 = boto3.client("s3")


def run(cmd):
    check_call(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)


def aws_log():
    with open("/var/log/cloud-init-output.log") as f:
        return f.read()


def s3_put(key, value, content_type='text/plain'):
    r = s3.put_object(Bucket=BUCKET,
                      Key=key,
                      Body=value.encode('utf-8'),
                      ContentType=content_type)


def s3_get(key, default):
    try:
        r = s3.get_object(Bucket=BUCKET, Key=key)
        return str(r['Body'].read(), 'utf-8')
    except Exception as e:
        print(key, e)
        return default


def s3_all_keys(Prefix):
    ls = s3.list_objects_v2(Bucket=BUCKET, Prefix=Prefix, MaxKeys=10000)
    keys = []
    while True:
        contents = [obj['Key'] for obj in ls.get('Contents',[])]
        keys.extend(contents)
        if not 'NextContinuationToken' in ls:
            break
        ls = s3.list_objects_v2(Bucket=BUCKET, Prefix=Prefix,
                                  ContinuationToken=ls['NextContinuationToken'],
                                  MaxKeys=10000)
    return keys


def run_all():
    now = datetime.datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    dirname = 'vm/%s' % now

    # upload AWS log to S3
    s3_put(dirname+'/cloud-init-output.log', aws_log())

    # pull/build/test
    os.chdir(expanduser("~"))
    run('git clone --depth=1 https://github.com/open-lambda/open-lambda.git')
    os.chdir(expanduser("open-lambda"))
    git_commit = check_output('git rev-parse HEAD', shell=True)
    s3_put(dirname+'/commit.txt', git_commit)

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

    # refresh summary
    gen_report()

    # kill the VM (it has been configured to terminate on shutdown)
    run('poweroff -f')


def href(s3_path):
    url = URL + s3_path
    return '<a href="{url}">{url}</a>'.format(url=url)


def gen_report():
    vms = set()
    for k in s3_all_keys("vm"):
        vms.add(k.split('/')[1])
    vms = sorted(vms, reverse=True)

    html = []
    html += ['<html>', '<body>']

    for vm in vms:
        result = s3_get('vm/%s/test.txt'%vm, 'unkown')
        html += ['<h3>%s</h3>' % vm]
        html += ['<ul>']
        html += ['<li>Result: <b>'+result+'</b>']
        html += ['<li>Commit: '+href('vm/%s/commit.txt'%vm)]
        html += ['<li>Cloud Log: '+href('vm/%s/cloud-init-output.log'%vm)]
        html += ['<li>Test Log: '+href('vm/%s/tests.out'%vm)]
        html += ['</ul>']

    html += ['</body>', '</html>']
    html = '\n'.join(html)

    s3_put('tests.html', html, 'text/html')

    return html


def main():
    if len(sys.argv) == 1:
        run_all()
    elif sys.argv[1] == 'report':
        print(gen_report())


if __name__ == '__main__':
    main()
