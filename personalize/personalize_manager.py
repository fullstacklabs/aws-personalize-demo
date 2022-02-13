import boto3
import json
import logging
import random
from time import sleep
import time
from datetime import datetime, timedelta
import csv

from botocore.retries import bucket
from personalize.movielens_ds_handler import MovieLensDSHandler
from personalize.dummy_interaction_manager import DummyInteractionsManager
from personalize.s3_manager import S3Manager
from personalize.data_manager import DataManager

class PersonalizeManager:    
    def __init__(self, data_set_group_name: str, data_set_schema_name: str, import_job_name: str,
                        bucket_name: str, role_name: str):
        self.logger = logging.getLogger(__name__)
        self.movielens_handler = MovieLensDSHandler()
        self.personalize = boto3.client('personalize')
        self.data_manager = DataManager()
        self.data_manager.data_set_group_name = data_set_group_name
        self.data_manager.data_set_schema_name = data_set_schema_name        
        self.data_manager.dataset_group_arn = None
        self.data_manager.interactions_dataset_arn = None
        self.data_manager.solution_arn = None
        self.data_manager.campaign_name = "personalize-demo-camp"
        #self.data_manager.solution_version_arn = "arn:aws:personalize:us-west-2:347817322228:solution/personalize-demo-soln-user-personalization/5cc5c628"
        self.data_manager.solution_version_arn = None
        self.data_manager.campaign_arn = None
        self.data_manager.import_job_name = import_job_name
        self.data_manager.recipe_arn = "arn:aws:personalize:::recipe/aws-user-personalization"
        self.solution_metrics_response = None

        self.s3_manager = S3Manager(data_manager=self.data_manager, bucket_id=bucket_name, role_name=role_name)                

    def load_data_manager(self, data_manager: DataManager):
        self.logger.info("Load data manager")
        self.data_manager = data_manager        
        self.s3_manager.load_data_manager(data_manager=data_manager)

    
    def setup_personalize_datasetgroup(self):
        data_manager = DummyInteractionsManager()
        number_users = 30
        data_manager.generate_dummy_interaction(1000)
        movies_ids = data_manager.get_movie_list()
        user_ids = data_manager.get_random_emails(number_users)
        print(len(user_ids))
        f = open('dataset/interactions.csv', 'w')
        writer = csv.writer(f)
        header = ['USER_ID', 'ITEM_ID', 'RATING', 'TIMESTAMP']        
        writer.writerow(header)
        index = 0
        for mid in movies_ids:
            print(index)
            data = [user_ids[index], mid, random.randrange(1,5,1), str(int(time.time()))]
            writer.writerow(data)
            if (index+1)>=number_users:
                index = 0
            else:
                index+=1
        f.close()
            

    def configure_personalize_dataset_group(self):
        self.logger.info("Configure create data set group")
        # Configure the SDK to Personalize:    
        create_dataset_group_response = self.personalize.create_dataset_group(
            name = self.data_manager.data_set_group_name
        )

        self.data_manager.dataset_group_arn = create_dataset_group_response['datasetGroupArn']
        self.logger.debug(json.dumps(create_dataset_group_response, indent=2))
        self.logger.info("After create data set group with arn: %s", self.data_manager.dataset_group_arn)
        time = datetime.now()
        max_time = time + timedelta(hours=5)    
        while time < max_time:        
            describe_dataset_group_response = self.personalize.describe_dataset_group(
                datasetGroupArn = self.data_manager.dataset_group_arn
            )
            status = describe_dataset_group_response["datasetGroup"]["status"]
            self.logger.info("DatasetGroup: {}".format(status))
        
            if status == "ACTIVE" or status == "CREATE FAILED":
                break
            
            sleep(60)
        

    def configure_dataset(self):
        self.logger.info("Before configure data set")
        interactions_schema = {
            "type": "record",
            "name": "Interactions",
            "namespace": "com.amazonaws.personalize.schema",
            "fields": [
            {
                "name": "USER_ID",
                "type": "string"
            },
            {
                "name": "ITEM_ID",
                "type": "string"
            },
            {
                "name": "RATING",
                "type": "int"
            },
            {
                "name": "TIMESTAMP",
                "type": "long"
            }
            ],
            "version": "1.0"
        }

        create_schema_response = self.personalize.create_schema(
            name = self.data_manager.data_set_schema_name,
            schema = json.dumps(interactions_schema)
        )

        interaction_schema_arn = create_schema_response['schemaArn']
        self.data_manager.schema_arn = interaction_schema_arn
        self.logger.debug(json.dumps(create_schema_response, indent=2))
        self.logger.info("After create the schema arn %s", self.data_manager.schema_arn)

        dataset_type = "INTERACTIONS"
        create_dataset_response = self.personalize.create_dataset(
            name = "personalize-demo-client-ints",
            datasetType = dataset_type,
            datasetGroupArn = self.data_manager.dataset_group_arn,
            schemaArn = interaction_schema_arn
        )

        self.data_manager.interactions_dataset_arn = create_dataset_response['datasetArn']
        self.logger.debug(json.dumps(create_dataset_response, indent=2))
        self.logger.info("After creation interactions data set %s", self.data_manager.interactions_dataset_arn)


    def configure_s3_interaction_dataset(self):
        self.s3_manager.create_bucket_s3()
        self.s3_manager.upload_file_to_s3(data_directory=self.movielens_handler.data_directory,
                        file_path=self.movielens_handler.interactions_filename)
        self.s3_manager.configure_bucket_policy()
        self.s3_manager.configure_iam_roles_personalize()


    def import_data_set_to_personalize(self):
        self.logger.info("Before import the data set to S3")
        create_dataset_import_job_response = self.personalize.create_dataset_import_job(
            jobName = self.data_manager.import_job_name,
            datasetArn = self.data_manager.interactions_dataset_arn,
            dataSource = {
                "dataLocation": "s3://{}/{}".format(self.data_manager.bucket_name,
                         self.movielens_handler.interactions_filename)
            },
            roleArn = self.data_manager.role_arn
        )

        dataset_import_job_arn = create_dataset_import_job_response['datasetImportJobArn']
        self.logger.debug(json.dumps(create_dataset_import_job_response, indent=2))
        self.logger.info("After creation the job for import: %s", dataset_import_job_arn)
        time = datetime.now()
        max_time = time + timedelta(hours=6)    
        while time < max_time:        
            describe_dataset_import_job_response = self.personalize.describe_dataset_import_job(
                datasetImportJobArn = dataset_import_job_arn
            )
            status = describe_dataset_import_job_response["datasetImportJob"]['status']
            self.logger.info("DatasetImportJob: {}".format(status))
    
            if status == "ACTIVE" or status == "CREATE FAILED":
                break
        
            sleep(60)



    def configure_personalize_solution(self):
        self.logger.info("Before create the personalize solution")
        create_solution_response = self.personalize.create_solution(
            name = "personalize-demo-soln-user-personalization",
            datasetGroupArn = self.data_manager.dataset_group_arn,
            recipeArn = self.data_manager.recipe_arn
        )

        self.data_manager.solution_arn = create_solution_response['solutionArn']
        self.logger.debug(json.dumps(create_solution_response, indent=2))        
        self.logger.info("After create the solution: %s", self.data_manager.solution_arn)

    def create_solution_version(self):
        self.logger.info("Before create the solution version")
        create_solution_version_response = self.personalize.create_solution_version(
            solutionArn = self.data_manager.solution_arn
        )

        self.data_manager.solution_version_arn = create_solution_version_response['solutionVersionArn']
        self.logger.debug(json.dumps(create_solution_version_response, indent=2))
        self.logger.info("After create the solution version: %s", self.data_manager.solution_version_arn)
        time = datetime.now()
        max_time = time + timedelta(hours=3)    
        while time < max_time:        
            describe_solution_version_response = self.personalize.describe_solution_version(
                  solutionVersionArn = self.data_manager.solution_version_arn
            )
            status = describe_solution_version_response["solutionVersion"]["status"]
            self.logger.info("SolutionVersion: {}".format(status))
            
            if status == "ACTIVE" or status == "CREATE FAILED":
                break
                
            sleep(60)        

    
    def evaluate_solution_version(self):
        self.logger.info("Before evaluate the solution version")
        solutions_metric_response = self.personalize.get_solution_metrics(
            solutionVersionArn = self.data_manager.solution_version_arn
        )

        self.logger.info(json.dumps(solutions_metric_response, indent=2))        
        

    def create_campaing(self):
        self.logger.info("Creating campaing...")
        create_campaign_response = self.personalize.create_campaign(
            name = self.data_manager.campaign_name,
            solutionVersionArn = self.data_manager.solution_version_arn,
            minProvisionedTPS = 1,
            campaignConfig = {
                "itemExplorationConfig": {
                "explorationWeight": "0.3",
                "explorationItemAgeCutOff": "30"
                }
            }
        )
        self.data_manager.campaign_arn = create_campaign_response['campaignArn']
        self.logger.debug(json.dumps(create_campaign_response, indent=2))
        self.logger.info("After create the campaing: %s", self.data_manager.campaign_arn)
        time = datetime.now()
        max_time = time + timedelta(hours=3)    
        while time < max_time:      
            describe_campaign_response = self.personalize.describe_campaign(
                campaignArn = self.data_manager.campaign_arn
            )
            status = describe_campaign_response["campaign"]["status"]
            self.logger.info("Campaign: {}".format(status))
        
            if status == "ACTIVE" or status == "CREATE FAILED":
                break
            
            sleep(60)
    
    def _cleanup_campaing(self):
        self.logger.info("Cleaning up the campaing %s", self.data_manager.campaign_arn)
        try:   
            self.personalize.delete_campaign(campaignArn=self.data_manager.campaign_arn)
            time = datetime.now()
            max_time = time + timedelta(hours=3)    
            while time < max_time:   
                try:   
                    describe_campaign_response = self.personalize.describe_campaign(
                        campaignArn = self.data_manager.campaign_arn
                    )
                    status = describe_campaign_response["campaign"]["status"]
                    self.logger.info("Campaign: {}".format(status))
                    if status != "DELETE IN_PROGRESS" and status != "DELETE PENDING":
                        break                                
                except Exception:
                    break
                sleep(60)
        except Exception:
            logging.error("Error on cleaning up campaing: %s", self.data_manager.campaign_arn)
    
    def _cleanup_solution(self):
        self.logger.info("Cleaning up the solution: %s", self.data_manager.solution_arn)
        try:
            self.personalize.delete_solution(
                solutionArn = self.data_manager.solution_arn
            )
            time = datetime.now()
            max_time = time + timedelta(hours=3)    
            while time < max_time:     
                try: 
                    describe_solution_response = self.personalize.describe_solution(
                        solutionVersionArn = self.data_manager.solution_arn
                    )
                    status = describe_solution_response["solution"]["status"]
                    self.logger.info("Solution: {}".format(status))
                    if status == "CREATE STOPPED":
                        break
                except Exception:
                    break
                sleep(60)
        except Exception:
            logging.error("Error on cleaning the solution: %s", self.data_manager.solution_arn)
    
    def _clean_up_dataset(self):
        self.logger.info("Cleaning up the data set: %s", self.data_manager.interactions_dataset_arn)
        try:
            delete_dataset_response = self.personalize.delete_dataset(            
                datasetArn = self.data_manager.interactions_dataset_arn,            
            )
            self.logger.debug(json.dumps(delete_dataset_response, indent=2))
            time = datetime.now()
            max_time = time + timedelta(minutes=30)    
            while time < max_time:        
                try: 
                    describe_data_set = self.personalize.describe_dataset(
                        datasetArn = self.data_manager.interactions_dataset_arn
                    )
                    status = describe_data_set["dataset"]["status"]
                    self.logger.info("Dataset Status: {}".format(status))
                
                    if status != "DELETE PENDING" and status!="DELETE IN_PROGRESS": 
                        break
                except Exception as e:                   
                    break
                
                sleep(60)
        except Exception as e:            
            logging.error("Error on cleaning the dataset: %s", self.data_manager.interactions_dataset_arn)
    
    def _clean_dataset_group(self):
        self.logger.info("Cleaning up the data set group: %s", self.data_manager.dataset_group_arn)
        try:
            delete_data_set_group = self.personalize.delete_dataset_group(
                datasetGroupArn=self.data_manager.dataset_group_arn
            )
            self.logger.debug(json.dumps(delete_data_set_group, indent=2))
            time = datetime.now()
            max_time = time + timedelta(minutes=30)    
            while time < max_time:        
                try: 
                    describe_dataset_group_response = self.personalize.describe_dataset_group(
                        datasetGroupArn = self.data_manager.dataset_group_arn
                    )
                    status = describe_dataset_group_response["datasetGroup"]["status"]
                    self.logger.info("DatasetGroup: {}".format(status))
                
                    if status != "DELETE PENDING":
                        break
                except Exception:
                    break
                
                sleep(60)
        except Exception as e:             
            logging.error("Error on cleaning the dataset group: %s", self.data_manager.dataset_group_arn)

    def _remove_schema(self):  
        try:
            self.logger.info("Cleaning up the schema: %s", self.data_manager.schema_arn)      
            self.personalize.delete_schema(schemaArn=self.data_manager.schema_arn)
        except Exception as e:            
            self.logger.error("Error cleaning up the schema")
        

    def cleanup(self):
        self.s3_manager.cleanup()
        self._cleanup_campaing()
        self._cleanup_solution()
        self._clean_up_dataset()
        self._remove_schema()
        self._clean_dataset_group()
        

    def store_data_manager(self):
        self.data_manager.save_data_to_json()

