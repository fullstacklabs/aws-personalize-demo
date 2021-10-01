import boto3
import json
import logging
from time import sleep

from botocore import exceptions
from personalize.data_manager import DataManager



# AmazonPersonalizeFullAccess provides access to any S3 bucket with a name that includes "personalize" or "Personalize" 
# if you would like to use a bucket with a different name, please consider creating and attaching a new policy
# that provides read access to your bucket or attaching the AmazonS3ReadOnlyAccess policy to the role
policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonPersonalizeFullAccess"
s3_policy_arn = 'arn:aws:iam::aws:policy/AmazonS3FullAccess'

class S3Manager:
    def __init__(self, bucket_id: str, role_name: str, data_manager: DataManager):       
        self.logger = logging.getLogger(__name__)
        self.data_manager = data_manager
        self.data_manager.bucket_id = bucket_id
        self.data_manager.bucket_name =  None
        self.data_manager.interactions_s3_data_path = None        
        self.data_manager.role_name = role_name
        self.data_manager.role_arn = None
    
    def load_data_manager(self, data_manager: DataManager):
        self.logger.info("Load data manager")
        self.data_manager = data_manager
    
    def create_bucket_s3(self):
        self.logger.info("Creating the S3 Bucket with name: %s", self.data_manager.bucket_id)
        session = boto3.session.Session()
        region = session.region_name
        s3 = boto3.client("s3")
        account_id =  boto3.client('sts').get_caller_identity().get('Account')
        self.data_manager.bucket_name = account_id + "-" + region + "-" + self.data_manager.bucket_id
        self.logger.info("Before create the bucket: %s", self.data_manager.bucket_name)
        if region == "us-east-1":
            s3.create_bucket(Bucket=self.data_manager.bucket_name)
        else:
            s3.create_bucket(
                Bucket=self.data_manager.bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
         )    

    def upload_file_to_s3(self, data_directory: str, file_path: str):
        self.logger.info("Uploading file to S3: %s", file_path)
        interactions_file_path = data_directory + "/" + file_path        
        boto3.Session().resource('s3').Bucket(self.data_manager.bucket_name).Object(file_path).upload_file(interactions_file_path)
        self.data_manager.interactions_s3_data_path = "s3://"+self.data_manager.bucket_name+"/"+file_path        
        self.logger.info("Finishing uploading file to S3: %s", file_path)


    def configure_bucket_policy(self):
        self.logger.info("Configuring the bucket policy")
        s3 = boto3.client("s3")
        policy = {
            "Version": "2012-10-17",
            "Id": "PersonalizeS3BucketAccessPolicy",
            "Statement": [
                {
                    "Sid": "PersonalizeS3BucketAccessPolicy",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "personalize.amazonaws.com"
                    },
                    "Action": [
                        "s3:*Object",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "arn:aws:s3:::{}".format(self.data_manager.bucket_name),
                        "arn:aws:s3:::{}/*".format(self.data_manager.bucket_name)
                    ]
                }
            ]
        }

        s3.put_bucket_policy(Bucket=self.data_manager.bucket_name, Policy=json.dumps(policy))
        self.logger.info("After related the bucket policy")

    def configure_iam_roles_personalize(self):
        self.logger.info("Configure the IAM Roles for personalize")
        iam = boto3.client("iam")

    
        assume_role_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                "Effect": "Allow",
                "Principal": {
                    "Service": "personalize.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
                }
            ]
        }

        
        create_role_response = iam.create_role(
            RoleName = self.data_manager.role_name,
            AssumeRolePolicyDocument = json.dumps(assume_role_policy_document)
        )

        
        iam.attach_role_policy(
            RoleName = self.data_manager.role_name,
            PolicyArn = policy_arn
        )

        # Now add S3 support
        iam.attach_role_policy(
            PolicyArn=s3_policy_arn,
            RoleName=self.data_manager.role_name
        )
        sleep(60) # wait for a minute to allow IAM role policy attachment to propagate

        self.data_manager.role_arn = create_role_response["Role"]["Arn"]
        self.logger.info("Finishing attaching the role to the policy: %s", self.data_manager.role_arn)    

    def cleanup(self):
        try:
            self.logger.info("Cleaning up the S3 information")
            iam = boto3.client("iam")
            s3 = boto3.resource("s3")
            try:            
                iam.detach_role_policy(RoleName=self.data_manager.role_name,
                    PolicyArn=s3_policy_arn)
            except iam.exceptions.NoSuchEntityException:
                self.logger.error("Policiy %s doesn't exists", s3_policy_arn)
            try:            
                iam.detach_role_policy(RoleName=self.data_manager.role_name,
                    PolicyArn=policy_arn)
            except iam.exceptions.NoSuchEntityException:
                self.logger.error("Policiy %s doesn't exists", policy_arn)
            iam.delete_role(RoleName=self.data_manager.role_name)        
            bucket = s3.Bucket(name=self.data_manager.bucket_name)
            bucket.objects.all().delete()
            bucket.delete()
            self.logger.info("Finishing cleaning up the S3 information")
        except Exception as e:
            print(e)
            self.logger.error("Error on cleanup S3 resources ")
        

