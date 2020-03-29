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

def provision_cert(email, domain, sans):
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
      #TODO: Iterate over all the domains, this just does the first one
      first_domain = domain.split(',')[0]
      first_domain = first_domain.replace("*.","")
      path = '/tmp/config-dir/live/' + first_domain + '/'

      return {
            'certificate': read_and_delete_file(path + 'cert.pem'),
            'private_key': read_and_delete_file(path + 'privkey.pem'),
            'certificate_chain': read_and_delete_file(path + 'chain.pem')
      }

def read_and_delete_file(path):
      with open(path, 'r') as file:
            contents = file.read()
      os.remove(path)
      return contents

def getCert(domain):
      context = ssl.create_default_context()

      with socket.create_connection((domain, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                  return(ssock.getpeercert())

def getDaystoExpire(cert):

      expDatetime = parse(cert['notAfter'])
      expTime = abs((expDatetime - datetime.datetime.now(pytz.utc)).days)
      
      return expTime

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

##### MAIN#####

#Check if the domain is less than 15 days to expire.
#
domain='amerisure.com'
bucket='amic-ssl-certs'
email='rob@thefochts.com'

cert=getCert(domain)
print('Subject: '+getSslSubject(cert))
print('SANs: '+getSslSans(cert))
print('Days to Expire: '+str(getDaystoExpire(cert)) )


#if (timeVal < 20):
#      cert = provision_cert(email,domain)
#      saveCertToS3(bucket, domain, cert)
#      print(domain+' has been updated')




