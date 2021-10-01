import logging

from personalize.personalize_manager import PersonalizeManager
from personalize.data_manager import DataManager

logging.basicConfig(format='%(asctime)s-%(filename)s-%(module)s-%(funcName)s-%(levelname)s:%(message)s',
         filename="logs/personalize-cleanup.log", level="INFO")
logging.getLogger().addHandler(logging.StreamHandler())


data_manager = DataManager().load_data_to_json()
if data_manager is not None:
    personalize_manager = PersonalizeManager(None, None, None, bucket_name=None, role_name=None)
    personalize_manager.load_data_manager(data_manager=data_manager)

    personalize_manager.cleanup()
else:
    print("There's any personalize object to cleanup")