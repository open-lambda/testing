import os, sys, boto3, subprocess, time
from subprocess import check_call, check_output

ec2 = boto3.client('ec2')
IMAGE_NAME = 'ol-dev'
UBUNTU_AMI = "ami-0fb653ca2d3203ac1"

def run(cmd):
    check_call(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)


def list_amis():
    r = ec2.describe_images(Filters=[{"Name": "name", "Values": [IMAGE_NAME]}])
    return r


def delete_old(name):
    images = ec2.describe_images(Filters=[{"Name": "name", "Values": [name]}])["Images"]
    if len(images) == 0:
        return
    assert(len(images) == 1)

    img = images[0]
    image_id = img['ImageId']
    mappings = img['BlockDeviceMappings']

    ec2.deregister_image(ImageId=image_id)
    for row in mappings:
        snap_id = row.get('Ebs', {}).get('SnapshotId', None)
        if snap_id:
            r = ec2.delete_snapshot(SnapshotId=snap_id)
            print(r)


def ssh(cmd, ip, sudo=True):
    print(cmd)
    if sudo:
        cmd = "sudo " + cmd
    try:
        cmd = ["ssh", "-o StrictHostKeyChecking=no", f"ubuntu@{ip}", cmd]
        return str(subprocess.check_output(cmd, stderr=subprocess.STDOUT), "utf-8")
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise e


def main():
    # cleanup old image
    delete_old(IMAGE_NAME)

    # build new one
    res = ec2.run_instances(ImageId=UBUNTU_AMI,
                      MinCount=1, MaxCount=1,
                      InstanceType="t2.micro",
                      IamInstanceProfile={"Name":"ol-test-vm"},
                      KeyName="id_rsa",
                      TagSpecifications=[{"ResourceType": "instance", "Tags":[{"Key":"ol", "Value":"ol-test-vm"}]}])
    iid = res["Instances"][0]["InstanceId"]
    print(f"starting {iid}")
    ec2.get_waiter("instance_running").wait(InstanceIds=[iid])
    print("INSTANCE READY!")

    inst = ec2.describe_instances(InstanceIds=[iid])["Reservations"][-1]["Instances"][0]
    ip, iid = inst["PublicIpAddress"], inst["InstanceId"]
    print(ip, iid)

    # ping until ready
    for i in range(60):
        try:
            ssh("pwd", ip)
            break
        except subprocess.CalledProcessError:
            time.sleep(1)

    cmds = """
    apt update
    apt upgrade -y
    apt update
    apt remove -y unattended-upgrades
    apt install -y python3-pip make gcc docker.io curl

    pip3 install boto3

    wget -q -O /tmp/go1.17.6.linux-amd64.tar.gz https://dl.google.com/go/go1.17.6.linux-amd64.tar.gz
    tar -C /usr/local -xzf /tmp/go1.17.6.linux-amd64.tar.gz
    ln -s /usr/local/go/bin/go /usr/bin/go
    """

    for cmd in cmds.split("\n"):
        cmd = cmd.strip()
        if cmd:
            print(ssh(cmd, ip))

    res = ec2.create_image(InstanceId=iid, Name=IMAGE_NAME)
    print(res)
    ec2.get_waiter("image_available").wait(Filters=[{"Name": "image-id", "Values": [res["ImageId"]]}])
    print("IMAGE READY!")

    ec2.terminate_instances(InstanceIds=[iid])

    # make AMI public
    ec2.modify_image_attribute(ImageId=res["ImageId"],
                               LaunchPermission={'Add': [{'Group': 'all'}]})

    with open("ami.txt", "w") as f:
        f.write(res["ImageId"].strip())

    # share AMI to github
    run('git add ami.txt')
    run('git commit -m "sync ami.txt to %s"' % res["ImageId"])
    run('git push')

if __name__ == '__main__':
    main()
