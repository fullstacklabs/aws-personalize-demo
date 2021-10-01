import json
import jsonpickle

class DataManager:
    def __init__(self):               
        self.bucket_name =  None
        self.interactions_s3_data_path = None        
        self.bucket_id = None
        self.role_arn = None                
        self.data_set_group_name = None
        self.data_set_schema_name = None
        self.dataset_group_arn = None
        self.interactions_dataset_arn = None     
        self.schema_arn = None   
        self.solution_arn = None        
        self.campaign_name = None
        self.solution_version_arn = None        
        self.campaign_arn = None
        self.import_job_name = None        
        self.recipe_arn = None  
    
    def save_data_to_json(self):        
        data_file = open('data/data.json', 'w')
        data_file.write(jsonpickle.encode(self))
        data_file.close()


    def load_data_to_json(self):
        try:
            data_file = open('data/data.json', 'r')
            data = data_file.read()
            data_file.close()
            return jsonpickle.decode(data)
        except FileNotFoundError:
            return None