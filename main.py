import certbot.main
import datetime
import os
import subprocess
import datetime
import socket
import ssl
import urllib.request, urllib.error, urllib.parse, json
from urllib.parse import urlparse
import OpenSSL
import datetime
import pytz
import boto3
from collections import defaultdict
from cryptography import x509
from dateutil.parser import parse
import shutil

def provisionCert(email, domain, sans):
      certbot.main.main([
      'certonly',                             
      '-n',                                  
      '--agree-tos',                          
      '--email', email,                       
      '--dns-dnsmadeeasy',                    
      '--dns-dnsmadeeasy-credentials', '/tmp/dnsmadeeasy.ini',
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

      return {
            'certificate': cert_value,
            'private_key': privkey_value,
            'certificate_chain': certchain_value,
            'full_chain': fullchain_value
      }

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

##### MAIN#####

# S3 Bucket Name
bucket='rlf-test-bucket'
#bucket='amic-ssl-certs'
# Filename with endpoints to check 
endpointFilename = 'endpointList.json'
# Cert Email address
email='rfocht@amerisure.com'

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
                  print('Saving a new cert for endpoint '+endPoint+' with SSL Subject CN '+endpointCertSubject+' to S3 bucket '+bucket)
                  saveCertToS3(bucket, endpointCertSubject, newCertObj)
            if certLocation == 'internalNetscaler':
                  print('Saving a new cert for endpoint '+endPoint+' with SSL Subject CN '+endpointCertSubject+' to Internal Netscaler')
            if certLocation == 'perimeterNetscaler':
                  print('Saving a new cert for endpoint '+endPoint+' with SSL Subject CN '+endpointCertSubject+' to Perimeter Netscaler')
      else:
            print('The endpoint '+endPoint+' with SSL Subject CN '+endpointCertSubject+' does not need updating')
