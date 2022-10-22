import boto3

ec2 = boto3.client('ec2')
mail = boto3.client('sns')

sns_arn = "arn:aws:sns:ap-south-1:753809741141:EC2_Running_Topic"

ids = []
states = []
states_id = []
ec2_ids = []
ec2_tags = []



data = ec2.describe_instances()


i = data['Reservations']



for j in i:

    k = j['Instances']
    state = k[0]['State']['Name']
    states.append(state)



if 'stopped' in states:

        print("Something as Happened Might Be Some Instances Are Down")
        print("Below Instances with Tagged Are Down ")
        response = ec2.describe_instance_status(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['stopped']
                }
            ],
            IncludeAllInstances=True
        )



        for r in response['InstanceStatuses']:

            id = r['InstanceId']
            ec2_ids.append(id)


        l = 0

        while l < len(ec2_ids):

            tags = ec2.describe_tags(
                Filters=[
                    {
                        'Name': 'resource-id',
                        'Values': [ec2_ids[l]],
                    },
                ],
            )
            for t in tags['Tags']:
                ec2_tag = t['Key'], t['Value']
                ec2_tags.append(ec2_tag)


            msg = f'Alert! An EC2 Instance with Tags = {ec2_tags} is Stopped'
            print(msg)


            send_mail = mail.publish(
                TopicArn= sns_arn,
                Message= f'Your EC2 instance with Id  {ec2_ids[l]} with Tags = {ec2_tags} as Stopped',
                Subject= f'Alert! An EC2 Instance with Tags = {ec2_tags} is Stopped',
            )
            ec2_tags.clear()
            print(" Mail has Sent Successfully ")
            l += 1

else:

    print("ALL Instances Are Running")
    print("Everything Looks Fine")


print("END")
