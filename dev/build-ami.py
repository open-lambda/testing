import os, sys, boto3
from subprocess import check_call, check_output

ec2 = boto3.client('ec2')

IMAGE_NAME = 'ol-dev'

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


def main():
    # cleanup old image
    delete_old(IMAGE_NAME)

    # build new one
    run('vagrant up')
    run('vagrant create-ami --name ' + IMAGE_NAME +
        ' --desc "dev VM for building/testing OpenLambda" --tags ol-vm=dev')
    run('vagrant destroy --force')

    # save AMI to file
    images = list_amis()["Images"]
    assert(len(images) == 1)
    ami = images[0]["ImageId"]
    with open("ami.txt", "w") as f:
        f.write(ami)

    # make AMI public
    ec2.modify_image_attribute(ImageId=ami,
                               LaunchPermission={'Add': [{'Group': 'all'}]})

    # share AMI to github
    run('git add ami.txt')
    run('git commit -m "sync ami.txt to %s"' % ami)
    run('git push')

if __name__ == '__main__':
    main()
