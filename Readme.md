# Python script to check list of Certs and renew those that are less than 20 days to expire.

1. _getDomainsToCheck_ from an S3 bucket file named _endpointList.json_
            JSON formtted file. Location can be S3 | perimeterNetscaler | internalNetscaler
            {"domain1":"location",
            "domain2":"location"}
2. For each domain, do the follwoing:
      a. _getCert_ for each domain
      b. If the cert _shouldBeProvisioned_ then  
      c. _provisionCert_ by providing the email, sslSubject and sans
            - provisioned cert will have the subjectCN set to domain, SANs as listed in sans, email as provdied. 
            - returns a cert object containing: 'certificate' , 'private_key' and 'certificate_chain'
      d. If location is _s3_ then _saveCertsToS3Bucket_ specifying the bucket, domain and cert object


# Utilities:
 1. buildZip.sh - assuming you have a backup copy of the Python virutla env tored in lets_encrypt.zip.bak2, this
                  will copy that and add the main.py to it, then upload that zip file to the lambda funciton using the aws cli.
                  Shoudld get back a "LastUpdateStatus": "Successful" response from the CLI. 

# Implementation Notes

## Used an AWS Step Function named _certbot-run_ (`certbot-run.json`) to control the overall flow:
### Step function States:
      1. Build Certbot Env
      2. Run Certbot-dme
      3. Destroy certbot env
### Each of these states has these corresponding lambda function (and repo code) named:
      1. build-certbot-env (`build-certbot-end.py`)
      2. certbot-dme (`main.py`)
      3. destroy-certbot-end.py (`destroy-certbot-end`)  
### Step Function IAM Roles Needed:
      - State Machines needs: XrayAccess(automatically created), LambdaInvoke
      - Lambda Funcitons: Lambda Basic(automatically created), StepFunction, EC2, S3, secrets
      - basic policy created was: certbot-dme-policy
      - Added this to the Basic AWS lambda policies that were autmatically created for the role. 

## Used a CloudWatch event to trigger the _certbot_run_ step function each week day at 9PM (0 1 ? * TUE-SAT *).

# Building the Python Virtual Environment

Create an AWS EC2 with AWS Linux 2 using t2.micro
Then do this on it....

`sudo yum install python3`     (python 3.7 was the latest when this was done)
`sudo pip3 install virtualenv`

`cd `    //to be sure your in the ec2-user home
`virtualenv -p /usr/bin/python3.7 env`   //create the virtual env folder structure

`vi requirements.txt`  //add these to the file:
      certbot
      certbot-dns-route53
      certbot-dns-dnsmadeeasy
      cryptography
      datetime
      sockets
            
`source env/bin/activate`   //activate the virtual env
`pip3 install -r requirements.txt`
`deactivate`

In order to allow for the DNS to propogate. I had to modify the DNSMadeEasy plugin 
to set the TTL to 120 seconds, and then use a 90 second wait time for the certbot client.  
      - This was changed in the virtual env in the dns_dnsmadeeasy.py file here:
            ~/env/lib/python3.7/site-packages/certbot_dns_dnsmadeeasy/_internal/dns_dnsmadeeasy.py
            on line 27 `ttl = 120`

## Add the site-packages from the lib and lib64 directories to the zip file:
`cd env/lib/python3.7/site-packages`
`zip -r ~/lets_encrypt.zip .`

`cd  ~/env/lib64/python3.7/site-packages`
`zip -rg ~/lets_encrypt.zip .`

## Scp the zip file to your mac (from your local mac)
`scp -i ~/.ssh/SonarqubeKeys.pem ec2-user@{EC2 instance IP}:~/lets_encrypt.zip .`

## Add main.py to the zip file
`zip -g lets_encrypt.zip main.py`

## Upload to S3
