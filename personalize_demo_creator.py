import logging

from personalize.personalize_manager import PersonalizeManager
from personalize.data_manager import DataManager

DATA_SET_GROUP_NAME = "personalize-demo-movielens"
DATA_SET_SCHEMA_NAME = "personalize-demo-movielens-interactions"
IMPORT_JOB_NAME="personalize-demo-import"
DATASET_BUCKET_NAME = "personalize-demo-test"
BUCKET_ROLE_NAME = "PersonalizeRolePOC"

logging.basicConfig(format='%(asctime)s-%(filename)s-%(module)s-%(funcName)s-%(levelname)s:%(message)s',
         filename="logs/personalize-creator.log", level="INFO")
logging.getLogger().addHandler(logging.StreamHandler())

personalize_manager = PersonalizeManager(data_set_group_name=DATA_SET_GROUP_NAME,
                data_set_schema_name=DATA_SET_SCHEMA_NAME, import_job_name=IMPORT_JOB_NAME,
                bucket_name=DATASET_BUCKET_NAME, role_name=BUCKET_ROLE_NAME)
personalize_manager.setup_personalize_datasetgroup()
personalize_manager.configure_personalize_dataset_group()
personalize_manager.configure_dataset()
personalize_manager.configure_s3_interaction_dataset()
personalize_manager.import_data_set_to_personalize()
personalize_manager.configure_personalize_solution()
personalize_manager.create_solution_version()
personalize_manager.evaluate_solution_version()
personalize_manager.create_campaing()
personalize_manager.store_data_manager()