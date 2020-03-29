# Python script to check list of Certs and renew those that are less than 20 days to expire.

1. getDomainsToCheck from an S3 bucket file named sslDomains
            JSON formtted file. Location can be S3 | perimeterNetscaler | internalNetscaler
            {"domain1":"location",
            "domain2":"location"}
2. For each domain, do the follwoing:
      a. getCert for each domain
      b. If the cert shouldBeProvisioned then  
      c. provisionCert by providing the email, domain and sans
            - provisioned cert will have the subjectCN set to domain, SANs as listed in sans, email as provdied. 
            - returns a cert object containing: 'certificate' , 'private_key' and 'certificate_chain'
      d. saveCertsToS3Bucket specifying the bucket, domain and cert object