#!/bin/bash
# This injects the main.py file into the python virtual environment 
# (which is in lets_encrypt.zip.bak2). 
# Then refreshes the AWS credentials and
# adds the zip file to the certbot-dme lambda function.  

# Copy lets_encrypt.zip.bak2 to lets_encrypt.zip
# Then add the main.py to it: zip -g lets_encrypt.zip main.py
cp lets_encrypt.zip.bak2 lets_encrypt.zip
zip -g lets_encrypt.zip main.py
. ~/assumeRoleIntSvcs 
aws lambda update-function-code \
      --function-name arn:aws:lambda:us-east-2:521718796648:function:certbot-dme \
      --zip-file fileb://lets_encrypt.zip