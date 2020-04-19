import boto3

def lambda_handler(event, context):

      routeTableId = 'rtb-0f557ae3731a55fcf'
   
      destroyNAT(event['Input']['natGatewayId'], routeTableId)
    
      client = boto3.client('stepfunctions')
      response = client.send_task_success(
            taskToken=event["TaskToken"],
            output="\"Success\""
      )

def destroyNAT(natGatewayId,routeTableId):
    
      client = boto3.client('ec2')
      print('Destroying NAT Gateway...')
      response = client.delete_nat_gateway(
            NatGatewayId=natGatewayId,
      )
      
      print('Destroying route to NAT gateway...')
      response = client.delete_route(
            DestinationCidrBlock='0.0.0.0/0',
            RouteTableId=routeTableId,
      )
