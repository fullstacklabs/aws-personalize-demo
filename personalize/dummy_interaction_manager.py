import requests
import math
import random
import string

class DummyInteractionsManager:
    TB_MOVIE_API_KEY = "b0087117f5c696b51297c5b60fef8615"
    def __init__(self):
        self.movie_list = []
        self.random_emails = []
    
    def generate_dummy_interaction(self, number_entities):
        
        stop_index = math.floor(number_entities/20)
        
        for i in range(stop_index):
            print(f"Requesting {i+1} of {stop_index}")
            response = requests.get(f"https://api.themoviedb.org/3/discover/movie?api_key={self.TB_MOVIE_API_KEY}&language=en&page={i+1}")
            response_json = response.json()            
            self.append_list(response_json["results"])
    
    def append_list(self, list_movies):
        for movie in list_movies:
            self.movie_list.append(movie["id"])
            
    def get_movie_list(self):
        return self.movie_list
            
    def get_random_emails(self, number_emails):
        for _ in range(number_emails):
            self.random_emails.append(self.random_char(10)+"@gmail.com")
        return self.random_emails
        
    def random_char(self, char_num):
        return ''.join(random.choice(string.ascii_letters) for _ in range(char_num))

    
    