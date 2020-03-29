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
      '--config-dir', '/tmp/config-dir/',
      '--work-dir', '/tmp/work-dir/',
      '--logs-dir', '/tmp/logs-dir/',
      ])

      first_domain = domain.split(',')[0]
      first_domain = first_domain.replace("*.","")
      path = '/tmp/config-dir/live/' + first_domain + '/'

      return {
            'certificate': readDeleteFile(path + 'cert.pem'),
            'private_key': readDeleteFile(path + 'privkey.pem'),
            'certificate_chain': readDeleteFile(path + 'chain.pem')
      }

def readDeleteFile(path):
      with open(path, 'r') as file:
            contents = file.read()
      os.remove(path)
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
      
      return True if expTime < 20  else  False

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
      
      s3.Object(bucket, domain.replace('*.', '', 1)+'.crt').put(Body=cert['certificate'])
      s3.Object(bucket, domain.replace('*.', '', 1)+'.key').put(Body=cert['private_key'])
      
      return None

def getDomainsToCheck(bucket, filename):
      
      s3 = boto3.resource(service_name = 's3')

      s3Object = s3.Object(bucket, filename)
      config =  s3Object.get()['Body'].read()
      return(json.loads(config))

##### MAIN#####

#Check if the domain is less than 15 days to expire.
#

bucket='rlf-test-bucket'
email='rob@thefochts.com'

allDomains = getDomainsToCheck(bucket, 'sslDomains')

for domainName in allDomains:
      print('Working on '+domainName)
      location = str(allDomains[domainName])
      cert = getCert(domainName)
      if shoudlBeProvisioned(cert):
            print('getting new cert for '+domainName)
            newCertObj = provisionCert(email, domainName, getSslSans(cert))
            if location == 's3':
                  print('Saving new cert to S3')
                  saveCertToS3(bucket, domainName, newCertObj)
            if location == 'internalNetscaler':
                  print('Saving new cert to Internal Netscaler')
            if location == 'perimeterNetscaler':
                  print('Saving new cert to Perimeter Netscaler')
      else:
            print(domainName+' does not need updating')
