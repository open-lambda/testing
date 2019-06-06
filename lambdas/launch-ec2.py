import os, sys, json, datetime, boto3, requests

def main(event, context):
    s3 = boto3.client("s3")
    ec2 = boto3.client("ec2")

    # safeguards to avoid creating too many VMs and causing a big bill
    prev = ec2.describe_instances(Filters=[{"Name":"tag:ol" ,"Values":["ol-test-vm"]},
                                           {"Name":"instance-state-name", "Values":["running", "pending"]}])
    if len(prev["Reservations"]) > 0:
        return str(prev)
        
    prev = ec2.describe_instances()
    if len(prev) > 10:
        return prev

    # fetch VM image ID, and the script we will want to run on that VM
    r = requests.get("https://raw.githubusercontent.com/open-lambda/testing/master/dev-build/ami.txt")
    r.raise_for_status()
    ami = r.text

    r = requests.get("https://raw.githubusercontent.com/open-lambda/testing/master/tests/ec2-test.py")
    r.raise_for_status()
    script = r.text

    script = script.replace("DATA = {}", "DATA = " + repr(event))

    # launch one VM to do the testing.  When it is done, the VM will
    # upload results to S3 and self-destruct.
    ec2.run_instances(ImageId=ami,
                      MinCount=1, MaxCount=1,
                      InstanceType="t2.micro",
                      IamInstanceProfile={"Name":"ol-test-vm"},
                      KeyName="id_rsa",
                      InstanceInitiatedShutdownBehavior='terminate',
                      TagSpecifications=[{"ResourceType": "instance", "Tags":[{"Key":"ol", "Value":"ol-test-vm"}]}],
                      UserData=script)

    return {
        'statusCode': 200,
        'body': json.dumps('Yay, launched the VM!')
    }
