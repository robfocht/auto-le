import certbot.main
import cryptography
import datetime
import socket
import json
import ssl
import pytz
import boto3
import shutil
import base64
import os, stat
from collections import defaultdict
from dateutil.parser import parse
from botocore.exceptions import ClientError

def provisionCert(email, domain, sans):
      
      #grab DME credentials from AWS Secrets
      deleteFileIfExists('/tmp/dnsmadeeasy.ini')
      deleteDirIfExists('/tmp/config-dir/')
      deleteDirIfExists('/tmp/work-dir/')
      deleteDirIfExists('/tmp/logs-dir/')
      file = open('/tmp/dnsmadeeasy.ini','w') 
      file.write('dns_dnsmadeeasy_api_key = '+the_DME_secret()['API Key']+'\n') 
      file.write('dns_dnsmadeeasy_secret_key = '+the_DME_secret()['Secret Key']+'\n')
      file.close() 
      os.chmod('/tmp/dnsmadeeasy.ini', stat.S_IREAD )

      certbot.main.main([
      'certonly',                             
      '-n',                                  
      '--agree-tos',                          
      '--email', email,                       
      '--dns-dnsmadeeasy',                    
      '--dns-dnsmadeeasy-credentials', '/tmp/dnsmadeeasy.ini',
      '--dns-dnsmadeeasy-propagation-seconds','90',
      '-d', domain, 
      '-d', sans,
      '--test-cert',                        
      '--config-dir', '/tmp/config-dir/',
      '--work-dir', '/tmp/work-dir/',
      '--logs-dir', '/tmp/logs-dir/',
      ])

      domain = domain.replace("*.","")
      path = '/tmp/config-dir/live/' + domain + '/'
      cert_value = readFile(path + 'cert.pem')
      privkey_value =  readFile(path + 'privkey.pem')
      certchain_value =  readFile(path + 'chain.pem')
      fullchain_value = readFile(path + 'fullchain.pem')

      #clean up
      shutil.rmtree('/tmp/config-dir/')
      shutil.rmtree('/tmp/work-dir/')
      shutil.rmtree('/tmp/logs-dir/')
      os.remove('/tmp/dnsmadeeasy.ini')

      return {
            'certificate': cert_value,
            'private_key': privkey_value,
            'certificate_chain': certchain_value,
            'full_chain': fullchain_value
      }

def deleteFileIfExists(filepath):
      if os.path.isfile(filepath):
            os.remove(filepath)

def deleteDirIfExists(dirpath):
      if os.path.exists(dirpath):
            shutil.rmtree(dirpath)

def readFile(path):
      with open(path, 'r') as file:
            contents = file.read()
      return contents

def getCert(domain):
      context = ssl.create_default_context()

      with socket.create_connection((domain, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                  return(ssock.getpeercert())

def shoudlBeProvisioned(cert):

      expDatetime = parse(cert['notAfter'])
      expTime = abs((expDatetime - datetime.datetime.now(pytz.utc)).days)
      print('Days to expire: '+str(expTime))
      
      return True if expTime < 70  else  False

def getSslSubject(cert):

     subject = dict(item[0] for item in cert['subject'])
     return((subject['commonName']))

def getSslSans(cert):
      
      subjectAltName = defaultdict(set)
      for type_, san in cert['subjectAltName']:
            subjectAltName[type_].add(san)
      sans = subjectAltName['DNS']

      return(", ".join(sans))

def saveCertToS3(bucket, domain, cert):
      
      s3 = boto3.resource(service_name = 's3')
      
      s3.Object(bucket, domain.replace('*.', '', 1)+'.crt').put(Body=cert['full_chain'])
      s3.Object(bucket, domain.replace('*.', '', 1)+'.key').put(Body=cert['private_key'])
      
      return None

def getEndpointsToCheck(bucket, filename):
      
      s3 = boto3.resource(service_name = 's3')

      s3Object = s3.Object(bucket, filename)
      config =  s3Object.get()['Body'].read()
      return(json.loads(config))

def the_DME_secret():

    secret_name = "DNSMadeEasy-API-Keys"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return(json.loads(secret))
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return(json.loads(decoded_binary_secret))

##### MAIN#####

#Uncomment this line and indent all lines below for Lambda
def handler(event, context):
      # S3 Bucket Name
      bucket = 'rlf-test-bucket'
      #bucket='amic-ssl-certs'
      # Filename with endpoints to check 
      endpointFilename = 'endpointList.json'
      # Cert Email address
      email='rfocht@amerisure.com'

      #Spin up the NAT gateway and assign the EIP
      # Pre-defined stuff:
      #     alocationId is the Id of the EIP to be reused and assigned to the NAT gateway
      #     subnetId is the subnet where the NAT gateway will be placed
      #     routeTableId is the route table for the certbot-private subnet that needs a 0.0.0.0/0 entry for the NAT Gateway
      allocationId = 'eipalloc-0e90668722b9b21b8'
      subnetId = 'subnet-037e77c0a52a8841a'
      routeTableId = 'rtb-0f557ae3731a55fcf'

      endPointsToCheck = getEndpointsToCheck(bucket, endpointFilename)

      for endPoint in endPointsToCheck:
            print('Working on endpoint: '+endPoint)
            certLocation = endPointsToCheck[endPoint]
            endpointCertObject = getCert(endPoint)
            endpointCertSubject = getSslSubject(endpointCertObject)
            if shoudlBeProvisioned(endpointCertObject):
                  print('getting new cert for '+endpointCertSubject)
                  newCertObj = provisionCert(email, endpointCertSubject, getSslSans(endpointCertObject))
                  if certLocation == 's3':
                        print('Saving a new cert for endpoint '+endPoint+' with SSL Subject CN= '+endpointCertSubject+' to S3 bucket '+bucket)
                        saveCertToS3(bucket, endpointCertSubject, newCertObj)
                  if certLocation == 'internalNetscaler':
                        print('Saving a new cert for endpoint '+endPoint+' with SSL Subject CN= '+endpointCertSubject+' to Internal Netscaler')
                  if certLocation == 'perimeterNetscaler':
                        print('Saving a new cert for endpoint '+endPoint+' with SSL Subject CN= '+endpointCertSubject+' to Perimeter Netscaler')
            else:
                  print('The endpoint '+endPoint+' with SSL Subject CN= '+endpointCertSubject+' does not need updating')

      return('Success')