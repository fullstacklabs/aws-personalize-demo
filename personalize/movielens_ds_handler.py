import os
import subprocess
import wget
from zipfile import ZipFile
import pandas as pd

class MovieLensDSHandler:
    def __init__(self):
        self.data_directory = "dataset"
        self.subdir_name = "ml-latest-small"
        self.interactions_filename = "interactions.csv"
        self.url = "http://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
        self.interactions_df = None
    
    def setup_datasource_data(self):
        
        if not os.path.isdir(self.data_directory):
            subprocess.call(["mkdir", self.data_directory])

        filename = wget.download(url=self.url, out=self.data_directory)
    
        with ZipFile(filename, 'r') as zipObj:
            zipObj.extractall(path=self.data_directory)


    def prepare_dataset(self):
    
        ratings_data = pd.read_csv(self.data_directory + os.path.sep +
             self.subdir_name + '/ratings.csv')
        ratings_data.head()

        filtered_watched = ratings_data.copy()
        filtered_watched = filtered_watched[filtered_watched['rating'] > 3]
        filtered_watched = ratings_data.copy()
        filtered_watched = filtered_watched[['userId', 'movieId', 'timestamp']]
        filtered_watched['EVENT_TYPE']='watch'

        filtered_clicked = ratings_data.copy()
        filtered_clicked = filtered_clicked[filtered_clicked['rating'] > 1]
        filtered_clicked = filtered_clicked[['userId', 'movieId', 'timestamp']]
        filtered_clicked['EVENT_TYPE']='click'

        self.interactions_df = filtered_clicked.copy()
        self.interactions_df = self.interactions_df.append(filtered_watched)
        self.interactions_df.sort_values("timestamp", axis = 0, ascending = True, 
                    inplace = True, na_position ='last')

        self.interactions_df.rename(columns = {'userId':'USER_ID', 'movieId':'ITEM_ID', 
                              'timestamp':'TIMESTAMP'}, inplace = True) 
    

    def write_data_set(self):
        self.interactions_df.to_csv((self.data_directory+
            os.path.sep+self.interactions_filename), 
                index=False, float_format='%.0f')        

