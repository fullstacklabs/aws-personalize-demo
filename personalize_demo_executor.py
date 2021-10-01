import boto3
import pandas as pd
import os
import logging
from personalize.data_manager import DataManager
from personalize.movielens_ds_handler import MovieLensDSHandler

personalize_runtime = boto3.client('personalize-runtime')

logging.basicConfig(format='%(asctime)s-%(filename)s-%(module)s-%(funcName)s-%(levelname)s:%(message)s',
         filename="logs/personalize-executor.log", level="INFO")
logging.getLogger().addHandler(logging.StreamHandler())

data_manager = DataManager().load_data_to_json()
if data_manager is not None:
    movielens_handler = MovieLensDSHandler()    
    movies = pd.read_csv(movielens_handler.data_directory + os.path.sep + movielens_handler.subdir_name + '/movies.csv', usecols=[0,1])
    movies['movieId'] = movies['movieId'].astype(str)
    movie_map = dict(movies.values)

    # Getting a random user:
    movielens_handler.prepare_dataset()
    user_id, item_id = movielens_handler.interactions_df[['USER_ID', 'ITEM_ID']].sample().values[0]

    get_recommendations_response = personalize_runtime.get_recommendations(
        campaignArn = data_manager.campaign_arn,
        userId = str(user_id),
    )
    # Update DF rendering
    pd.set_option('display.max_rows', 30)

    print("Recommendations for user: ", user_id)

    item_list = get_recommendations_response['itemList']

    recommendation_list = []

    for item in item_list:
        title = movie_map[item['itemId']]
        recommendation_list.append(title)

    print("Recomendations size: " + str(len(recommendation_list)))
    recommendations_df = pd.DataFrame(recommendation_list, columns = ['OriginalRecs'])
    print(recommendations_df)
else:
    print("Must create the personalize objects with: python3 personalize_demo_creator.py")
    