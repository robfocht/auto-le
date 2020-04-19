# Python script to check list of Certs and renew those that are less than 20 days to expire.

1. _getDomainsToCheck_ from an S3 bucket file named _sslDomains_
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


      1. Is the sonar cert valid?
      2. create nginx container that points to sonar.a,ersoiure.com
      3. Deploy noew nginx container
      

      Statemachine IAM Roles Needed:

      State mAchine needs: XrayAccess, LambdaInvoke
      Lambda Funcitons: Lambda Basic, StepFunction, EC2