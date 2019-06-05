#!/usr/bin/env python3
import os, sys, time, datetime, boto3
from subprocess import check_call, check_output
from os.path import expanduser, exists

with open(__file__) as f:
    print("SOURCE:")
    print("="*40)
    print(f.read())
    print("="*40)
    sys.stdout.flush()


BUCKET = 'open-lambda-public'
URL = 'https://s3.us-east-2.amazonaws.com/open-lambda-public/'
s3 = boto3.client("s3")
DATA = {}


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

    # move to user dir
    os.chdir(expanduser("~"))
    os.environ["HOME"] = expanduser("~") # why do we need to do this ourselves?

    # pull/build/test
    if not "commit" in DATA:
        run('git clone --depth=1 https://github.com/open-lambda/open-lambda.git')
    else:
        run(' && '.join([
            'git clone https://github.com/open-lambda/open-lambda.git',
            'cd open-lambda',
            'git checkout ' + DATA["commit"]
        ]))

    os.chdir("open-lambda")
    git_commit = check_output('git rev-parse HEAD', shell=True).decode('utf-8').strip()
    s3_put(dirname+'/commit.txt', git_commit)

    try:
        with open("build.out", "w", buffering=0) as f:
            check_call("make", shell=True, stdout=f, stderr=f)
        try:
            with open("tests.out", "w", buffering=0) as f:
                check_call("make test-all", shell=True, stdout=f, stderr=f)
                result = 'PASS'
        except:
            result = 'FAIL'
    except:
        result = 'BUILD-FAIL'

    # upload test results/logs to S3
    s3_put(dirname+'/test.txt', result)

    if exists('build.out'):
        with open('build.out') as f:
            s3_put(dirname+'/build.out', f.read())

    if exists('tests.out'):
        with open('tests.out') as f:
            s3_put(dirname+'/tests.out', f.read())

    if exists('test.json'):
        with open('test.json') as f:
            s3_put(dirname+'/test.json', f.read())

    if exists('testing/test-cluster/logs/worker-0.out'):
        with open("testing/test-cluster/logs/worker-0.out") as f:
            s3_put(dirname+'/worker-0.out', f.read())

    # refresh summary
    gen_report()

    # kill the VM (it has been configured to terminate on shutdown)
    run('poweroff -f')


def href(s3_path, all_keys):
    if not s3_path in all_keys:
        return '[NOT FOUND]'
    url = URL + s3_path
    return '<a href="{url}">{text}</a>'.format(url=url, text=url.split("/")[-1])


def gen_report():
    vms = set()
    all_keys = s3_all_keys("vm")
    for k in all_keys:
        vms.add(k.split('/')[1])
    vms = sorted(vms, reverse=True)

    html = []
    html += ['<html>', '<body>']

    for i, vm in enumerate(vms):
        if i < 14:
            commit = s3_get('vm/%s/commit.txt'%vm, 'unkown').strip()
            result = s3_get('vm/%s/test.txt'%vm, 'unkown').strip()
        else:
            # just so we can complete faster without doing too many S3 reads
            commit = '???'
            result = '???'

        html += ['<h3>%s [COMMIT: %s]</h3>' % (vm, commit)]
        html += ['<ul>']
        html += ['<li>Result: <b>'+result+'</b>']
        html += ['<li>Commit: '+href('vm/%s/commit.txt'%vm, all_keys)]
        html += ['<li>Cloud Log: '+href('vm/%s/cloud-init-output.log'%vm, all_keys)]
        html += ['<li>Build Log: '+href('vm/%s/build.out'%vm, all_keys)]
        html += ['<li>Test Log: '+href('vm/%s/tests.out'%vm, all_keys)]
        html += ['<li>Test Results: '+href('vm/%s/test.json'%vm, all_keys)]
        html += ['<li>Test Status: '+href('vm/%s/test.txt'%vm, all_keys)]
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
