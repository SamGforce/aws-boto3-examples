import boto3
import argparse
from cred_parser import loginInfo

# 3 mandatory Arguments are passed to this script. Insance key, key value, and action start/stop
# 4th arg is optionla, if not given will look for login.info inside same dir a the script
#this version expect loginInfo class to be in the lib file
parser = argparse.ArgumentParser(prog='myprogram')
parser.add_argument(
    '--tagKey', help='Specify the instance tag', type=str, required=True)
parser.add_argument(
    '--tagVal', help='Specify the instance tag', type=str, required=True)
parser.add_argument(
    '--action', help='Specify action to be take. Acceptable options: Stop/Start', type=str, required=True)
parser.add_argument('--credentialFile',
                    help='Specify the filne name containing credentials. Default is login.info', default='login.info', type=str)

args = parser.parse_args()
try:
    # here we are trying to catch any login failure; if not , at some point later boto spits out a bunch of nasty errors
    creds = loginInfo(args.credentialFile)
except Exception as e:
    print('Failed to retrieve credentials...', e)
    exit()
# for debug or testing, print credentials:
# print(creds.get_id(), creds.get_key())


def getEC2resourceObj(region='us-west-1'):
    # this fucntion returns the ec2 resource object for a given region
    try:
        ec2 = boto3.resource('ec2', region_name=region,
                             aws_access_key_id=creds.get_id(),
                             aws_secret_access_key=creds.get_key())
        return ec2
    except Exception as e:
        print('Failed to get EC2 resource', e)
        exit()


def getRegionNameList():
    # This function returns a list of regions based on response from AWS client object
    ec2_client = boto3.client('ec2')
    aws_regions = ec2_client.describe_regions()['Regions']
    regions = [x['RegionName'] for x in aws_regions]
    # print(regions)
    regions.reverse()
    return regions


def turnOffInstance(ec2, ID):
    # send EC2 resource object as well as ID to turn OFF
    try:
        ec2.Instance(ID).stop()
    except Exception as e:
        print(e)


def turnOnInstance(ec2, ID):
    # send EC2 resource object as well as ID to turn ON
    try:
        ec2.Instance(ID).start()
    except Exception as e:
        print(e)


def getInstanceIDbyTag(ec2, tagKey, tagVal):
    # send EC2 resource object as well as tag Key, and Value, get instance ID back
    instanceList = ec2.instances.filter()
    idList = []
    try:
        for instance in instanceList:
            for tag in instance.tags:
                if (tag['Key'] == tagKey):
                    if (tag['Value'] == tagVal):
                        # instanceID=instance.id
                        # print(instanceID)
                        idList.append(instance.id)
    except Exception as e:
        print(e)
        exit()
    return idList


# List of regions saved to a variable
regionList = getRegionNameList()

# We are going to go region by region, look for instances with matching tags and values, then do the start/stop action
for region in regionList:
    ec2 = getEC2resourceObj(region)
    idList = getInstanceIDbyTag(ec2, args.tagKey, args.tagVal)
    print('Searching in', region)
    if idList == []:
        #print('None found')
        pass
    elif args.action == 'Start':
        print('Instances found in', region, ':')
        for id in idList:
            print(id)
            turnOnInstance(ec2, id)
        print('Starting them up...')
    elif args.action == 'Stop':
        print('Instances found in', region, ':')
        for id in idList:
            print(id)
            turnOffInstance(ec2, id)
        print('Stopping EC2instances ...')
