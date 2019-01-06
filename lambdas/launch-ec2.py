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
    
    # get latest test config
    r = requests.get("https://raw.githubusercontent.com/open-lambda/testing/master/dev/ami.txt")
    r.raise_for_status()
    ami = r.text
    
    startup = """
#!/bin/bash
curl https://raw.githubusercontent.com/open-lambda/testing/master/dev-deploy/test.py -o test.py
python3 test.py
    """

    # TODO: grab ImageId from github; grab test.py from github
    ec2.run_instances(ImageId=ami,
                      MinCount=1, MaxCount=1,
                      InstanceType="t2.micro",
                      IamInstanceProfile={"Name":"ol-test-vm"},
                      KeyName="id_rsa",
                      InstanceInitiatedShutdownBehavior='terminate',
                      TagSpecifications=[{"ResourceType": "instance", "Tags":[{"Key":"ol", "Value":"ol-test-vm"}]}],
                      UserData=startup.strip())
    
    now = datetime.datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    dirname = 'lambda/%s' % now
    s3.put_object(Bucket="open-lambda-public", Key=dirname+"/executed")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda 3!')
    }
