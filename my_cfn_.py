#!/usr/bin/env python
from troposphere import Base64, GetAtt, FindInMap
from troposphere import Output, Ref, Template, Parameter
import troposphere.ec2 as ec2
import boto3
from botocore.exceptions import EndpointConnectionError

region_name=raw_input("Enter region name e.g.(us-west-2). default = us-west-2 : ")
if not region_name:
	region_name='us-west-2'
	
instance = boto3.resource('ec2', region_name )


def choose_keypair():
	kp_name=[]
	#Populating the declared list with objects of respective resource
	for keys in instance.key_pairs.all():
		kp_name.append(keys.key_name)
	#Loop for displaying list to select from
	for kp_iter in range(len(kp_name)):
		print str(kp_iter)+") "+ str(kp_name[kp_iter])
	
	kp_selection = raw_input("Please select number of keypair from list: ")
	
	if not kp_selection:
		kp_selection= 0
	return str(kp_name[int(kp_selection)])


def choose_subnet():
	sn_id=[]
	sn_az=[]
	#Populating the declared list with objects of respective resource
	for all in instance.subnets.all():
		sn_id.append(all.id);sn_az.append(all.availability_zone)
	#Loop for displaying list to select from
	for sn_iter in range(len(sn_id)):
		print str(sn_iter)+") "+ str(sn_id[sn_iter]) +" "+ str(sn_az[sn_iter])
	sn_selection = raw_input("Please choose the number of subnet from given list: ")
	sn_id_value=sn_id[int(sn_selection)]
	return sn_id_value
		

def choose_sg():
	try:
		sg_id=[]
		sg_group_name=[]
		#Populating the declared list with objects of respective resource
		for iter in instance.security_groups.all():
			#sg.append(str(iter.id)+" "+str(iter.group_name))
			sg_id.append(str(iter.id))
			sg_group_name.append(str(iter.group_name))
	except EndpointConnectionError as e:
		print e
		sys.exit(1)
	
	#Loop for displaying list to select from
	for i in range(len(sg_id)):
		print str(i)+") "+ str(sg_id[i]) +" "+ str(sg_group_name[i])

	selection=raw_input("Enter number from above list to select SG: ")
	try:
		sg_param_value=sg_id[int(selection)]
		print "You selected SG: "+ str(sg_param_value)
		return str(sg_param_value)
		
	except IndexError as e:
		print e


#THIS PART OF THE PROGRAM IS FOR GENERATING A CLOUDFORMATION TEMPLATE USING TROPOSPHERE MODULE 

try:
        #Instantiate a Template object
	template=Template()
        #Instantiating and populating PARAMETERS FOR Cloudformation Stack
	keyname_param= template.add_parameter(Parameter("KeyName", Description="Valid KeyName", Type="AWS::EC2::KeyPair::KeyName"))
	subnet_param = template.add_parameter(Parameter("Subnet",Description="Choose subnet", Type="AWS::EC2::Subnet::Id"))
	sg_param = template.add_parameter(Parameter("SecurityGroups",Description="Choose security group",Type="AWS::EC2::SecurityGroup::Id"))
	instancetype_param = template.add_parameter(Parameter("InstanceType",Description="Valid EC2 types", Type="String", Default="t2.micro", AllowedValues = ["t2.nano","t2.small","t2.micro"]))

	#ADDING REGION TO AMI MAPPING SO THAT CLOUDFORMATINO KNOWS WHICH AMI TO LAUNCH IN WHICH REGION
	template.add_mapping('RegionMap', {
	"us-east-1":	{ "AMI": "ami-0932686c"},
	"us-east-2":	{ "AMI": "ami-0932686c"},
	"us-west-2":	{ "AMI": "ami-f173cc91"}
})


	#CREATING A CLOUDFORMATINO TEMPLATE RESOURCE BY PASSING THE PARAMETERS AND MAPPING OBJECTS
	ec2_instance = template.add_resource(ec2.Instance( "myinstance", 
		ImageId=FindInMap("RegionMap", Ref("AWS::Region"),"AMI"), 
		SubnetId=Ref(subnet_param),
		InstanceType= Ref(instancetype_param),
		KeyName=Ref(keyname_param),
		SecurityGroupIds=[Ref(sg_param)],
		UserData=Base64("""#!/bin/bash 
yum update -y
yum install httpd -y
service httpd start"""
)))

	#OUTPUT FOR DATA TO RETURN AFTER SUCCESSFUL CREATION OF STACK SUCH AS PUBLIC DNS NAME, PUBLIC IP ETC
	template.add_output([
    Output(
        "InstanceId",
        Description="InstanceId of the newly created EC2 instance",
        Value=Ref(ec2_instance),
    ),
    Output(
        "AZ",
        Description="Availability Zone of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "AvailabilityZone"),
    ),
    Output(
        "PublicIP",
        Description="Public IP address of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PublicIp"),
    ),
    Output(
        "PrivateIP",
        Description="Private IP address of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PrivateIp"),
    ),
    Output(
        "PublicDNS",
        Description="Public DNSName of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PublicDnsName"),
    ),
    Output(
        "PrivateDNS",
        Description="Private DNSName of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PrivateDnsName"),
    ),
])


	#print(template.to_json())
	#TAKE STACK NAME INPUT FROM USER, KEEP ASKING UNTIL A STRING IS GIVEN
	boto3.setup_default_session(region_name = region_name)
	client = boto3.client("cloudformation")
	while True:
		stack_name = raw_input("Please enter a unique stack-name, which you have not already used: ")
		if not stack_name:
			print "Stack name required"
			continue
		else:
			break
	
	#USING A BOTO3 low level client of Cloudformation to issue the stack creation API call and fed the json template via to_json() call on the template object to boto3 client
	response = client.create_stack(
		StackName = stack_name,
		TemplateBody = template.to_json(),
		Parameters=[{
			'ParameterKey': 'SecurityGroups',
			'ParameterValue': choose_sg()
		},
		{
			'ParameterKey': 'Subnet',
			'ParameterValue': choose_subnet()
		},
		{
			'ParameterKey': 'KeyName',
			'ParameterValue': choose_keypair()
		}

])

		
except Exception as e:
	print e





