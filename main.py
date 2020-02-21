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
from datetime import date


def provision_cert(email, domains):
      certbot.main.main([
      'certonly',                             
      '-n',                                   
      '--agree-tos',                          
      '--email', email,                       
      '--dns-dnsmadeeasy',                    
      '--dns-dnsmadeeasy-credentials', '/tmp/dnsmadeeasy.ini',
      '-d', domains,                          
      '--config-dir', '/tmp/config-dir/',
      '--work-dir', '/tmp/work-dir/',
      '--logs-dir', '/tmp/logs-dir/',
      ])
      #TODO: Iterate over all the domains, this just does the first one
      first_domain = domains.split(',')[0]
      first_domain = first_domain.replace("*.","")
      path = '/tmp/config-dir/live/' + first_domain + '/'

      return {
      'certificate': readFile(path + 'cert.pem'),
      'private_key': readFile(path + 'privkey.pem'),
      'certificate_chain': readFile(path + 'chain.pem')
      }

def readFile(path):
      with open(path, 'r') as file:
            contents = file.read()
      return contents

def ssl_expiry_datetime(hostname):
    ssl_date_fmt = r'%b %d %H:%M:%S %Y %Z'

    context = ssl.create_default_context()
    conn = context.wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=hostname,
    )
    # 3 second timeout because Lambda has runtime limitations
    conn.settimeout(3.0)

    conn.connect((hostname, 443))
    ssl_info = conn.getpeercert()
    print(ssl_info)
    # parse the string from the certificate into a Python datetime object
    return datetime.datetime.strptime(ssl_info['notAfter'], ssl_date_fmt)


def getDaystoExpire(domain):
      now = date.today()
      # get SSL Cert info
      cert = ssl.get_server_certificate((domain, 443))
      x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
      x509info = x509.get_notAfter()

      exp_day = int(x509info[6:8].decode('utf-8'))
      exp_month = int(x509info[4:6].decode('utf-8'))
      exp_year = int(x509info[:4].decode('utf-8'))

      expDatetime  = date(exp_year,exp_month,exp_day)

      expTime = abs((expDatetime - now).days)
      return expTime

##### MAIN#####

#Check if the domain is less than 15 days to expire.
#If it is, then generate new certs
domain = 'thefochts.com'
timeVal = getDaystoExpire(domain)
print (timeVal)

if (timeVal < 15) 



cert = provision_cert('rfocht@amerisure.com','*.amerisure.com')
print (cert['certificate'])
print (cert['private_key'])
print (cert['certificate_chain'])

