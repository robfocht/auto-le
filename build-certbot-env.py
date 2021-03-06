import boto3


def lambda_handler(event, context):

#Spin up the NAT gateway and assign the EIP
# Pre-defined stuff:
#     - alocationId is the Id of the EIP to be reused and assigned to the NAT gateway
#     - subnetId is the subnet where the NAT gateway will be placed. In our case this is the certbot-private subnet
#     - routeTableId is the route table for the certbot-private subnet that needs a 0.0.0.0/0 entry for the NAT Gateway. 
#       In our case this is the certbot-provate-rt route table
    
      allocationId = 'eipalloc-0e90668722b9b21b8'
      subnetId = 'subnet-037e77c0a52a8841a'
      routeTableId = 'rtb-0f557ae3731a55fcf'
    
      ourNatGateway = buildNat(allocationId, subnetId, routeTableId)

      client = boto3.client('stepfunctions')
      response = client.send_task_success(
            taskToken=event["TaskToken"],
            output="\""+ourNatGateway+"\""
      )


def buildNat(allocationId,subnetId,routeTableId):
    
      client = boto3.client('ec2')
      ec2 = boto3.resource('ec2')
      print('Creating NAT gateway (this may take a minute or two)...')
      nat_response = client.create_nat_gateway(
            AllocationId=allocationId,
            SubnetId=subnetId,
            TagSpecifications=[{
                  'ResourceType': 'natgateway',
                  'Tags': [{
                        'Key': 'Name',
                        'Value': 'certbot-dme-natgw'
                        },]
            },]
      )
      
      waiter = client.get_waiter('nat_gateway_available')
      waiter.wait(
            NatGatewayIds=[nat_response['NatGateway']['NatGatewayId']],
            WaiterConfig={ 'Delay': 15,'MaxAttempts': 75 }
      )
      
      print('NAT gateway '+nat_response['NatGateway']['NatGatewayId']+'is up. Adding routes to '+routeTableId)
      
      route_table = ec2.RouteTable(routeTableId)
      route = route_table.create_route(
            DestinationCidrBlock='0.0.0.0/0',
            NatGatewayId=nat_response['NatGateway']['NatGatewayId'],
      )
      
      return(nat_response['NatGateway']['NatGatewayId'])