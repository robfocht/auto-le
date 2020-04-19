import boto3

def lambda_handler(event, context):
      print(event)
      print(event['Input']['natGatewayId'])
      client = boto3.client('stepfunctions')
      response = client.send_task_success(
            taskToken=event["TaskToken"],
            output="\""+event['Input']['natGatewayId']+"\""
      )