import pandas as pd
import numpy as np
from datamodels import ConfigFile
import random
from loguru import logger
from deap import base, creator, tools
import json
import os

class PlaylistOptimizer():
    def __init__(self) -> None:
        self.playlist = None

        config_file_path = os.getenv('config_file_path')

        with open(config_file_path) as f:
            self.config = json.load(f)

        self.config = ConfigFile(**self.config)

        for attr, value in self.config.general.model_dump().items():
            setattr(self, attr, value)
        
        self.optmization_weights = self.config.general.Optmization_weights
        self.default_optimization_parameters = self.config.general.default_optimization_parameters
        
        self.__initate_toolbox()

    # Calculate the features of the setlist
    def calculate_setlist_features(self, setlist: pd.DataFrame)->dict:
        '''function to calculate the features of a setlist
        '''
        total_duration_minutes = setlist['duration_ms'].sum()/1000/60
        setlist_popularity = setlist['popularity'].mean()
        setlist_genre_proportion = setlist['genre'].value_counts(normalize=True).to_dict()
        setlist_country_proportion = setlist['country'].value_counts(normalize=True).to_dict()
        setlist_decade_proportion = setlist['decade'].value_counts(normalize=True).to_dict()
        setlist_songs_per_artist = setlist['artists'].value_counts().max()
        setlist_target_features = setlist[['danceability', 'energy', 'loudness', 'valence']].mean().to_dict()

        return {
            'total_duration_minutes': total_duration_minutes,
            'setlist_popularity': setlist_popularity,
            'setlist_genre_proportion': setlist_genre_proportion,
            'setlist_country_proportion': setlist_country_proportion,
            'setlist_decade_proportion': setlist_decade_proportion,
            'setlist_songs_per_artist': setlist_songs_per_artist,
            'setlist_target_features': setlist_target_features
        }


    # Define the fitness function
    def fitness_function(self,individual:list[list],debug=False)->float:
        '''function to calculate the fitness score of an individual setlist. The score should be minimized for the genetic algorithm to work properly.
        '''
       
        current_setlist = self.playlist.iloc[individual]
        total_duration_minutes = current_setlist['duration_ms'].sum()/1000/60
        
        setlist_popularity = current_setlist['popularity'].mean()

        setlist_genre_proportion = current_setlist['genre'].value_counts(normalize=True).to_dict()
        setlist_country_proportion = current_setlist['country'].value_counts(normalize=True).to_dict()
        setlist_decade_proportion = current_setlist['decade'].value_counts(normalize=True).to_dict()

        setlist_songs_per_artist = current_setlist['artists'].value_counts()

        setlist_target_features = current_setlist[['danceability', 'energy', 'loudness', 'valence']].mean().to_dict()

        # Calculate the fitness score
        fitness_score = 0

        # tolerance levels
        tolerance_l1 = 0.05
        tolerance_l2 = 0.1
        tolerance_l3 = 0.35

        # Calculate the fitness score based on the total duration of the setlist
        duration_score = 1-abs(total_duration_minutes - self.default_optimization_parameters.max_duration)/self.default_optimization_parameters.max_duration
        print(f"duration score: {duration_score}") if debug else None
        fitness_score += abs(self.optmization_weights['max_duration']*duration_score)

        # Calculate the fitness score based on the popularity of the setlist
        if setlist_popularity < self.default_optimization_parameters.minimum_popularity:
            print(f"popularity score: {setlist_popularity}") if debug else None
            fitness_score += (self.default_optimization_parameters.minimum_popularity - setlist_popularity)*self.optmization_weights['minimum_popularity']
            

        # Calculate the fitness score based on the genre proportion of the setlist
        for genre, proportion in self.default_optimization_parameters.genre_proportion.items():
            genre_proportion = setlist_genre_proportion.get(genre)
            if genre_proportion is None:
                if proportion > 0:
                    print(f"genre {genre} is missing! equivalent score: 10000") if debug else None
                    fitness_score += 1e5
                continue
            if abs(genre_proportion - proportion) < tolerance_l1:
                continue
            elif abs(genre_proportion - proportion) < tolerance_l2:
                genre_score = self.optmization_weights['genre_proportion']*abs(genre_proportion - proportion)*10
            elif abs(genre_proportion - proportion) < tolerance_l3:
                genre_score = self.optmization_weights['genre_proportion']*abs(genre_proportion - proportion)*100
            else:
                genre_score = self.optmization_weights['genre_proportion']*abs(genre_proportion - proportion)*1000
                print(f"genre {genre} score: {genre_score}") if debug else None
                fitness_score += genre_score

        # Calculate the fitness score based on the country proportion of the setlist
        for country, proportion in self.default_optimization_parameters.country_proportion.items():
            country_proportion = setlist_country_proportion.get(country)
            if country_proportion is None:
                if proportion > 0:
                    print(f"country {country} is missing! equivalent score: 10000") if debug else None
                    fitness_score += 1e5
                continue
            if abs(country_proportion - proportion) < tolerance_l1:
                continue
            elif abs(country_proportion - proportion) < tolerance_l2:
                country_score = self.optmization_weights['country_proportion']*abs(country_proportion - proportion)*10
            elif abs(country_proportion - proportion) < tolerance_l3:
                country_score = self.optmization_weights['country_proportion']*abs(country_proportion - proportion)*100
            else:
                country_score = self.optmization_weights['country_proportion']*abs(country_proportion - proportion)*1000
                print(f"country {country} score: {country_score}") if debug else None
                fitness_score += country_score
        
        # Calculate the fitness score based on the decade proportion of the setlist
        for decade, proportion in self.default_optimization_parameters.decade_proportion.items():
            decade_proportion = setlist_decade_proportion.get(decade)
            if decade_proportion is None:
                if proportion > 0:
                    print(f"decade {decade} is missing! equivalent score: 100") if debug else None
                    fitness_score += 1e3
                continue
            if abs(decade_proportion - proportion) < tolerance_l1:
                continue
            elif abs(decade_proportion - proportion) < tolerance_l2:
                decade_score = self.optmization_weights['decade_proportion']*abs(decade_proportion - proportion)*10
            elif abs(decade_proportion - proportion) < tolerance_l3:
                decade_score = self.optmization_weights['decade_proportion']*abs(decade_proportion - proportion)*100
            else:
                decade_score = self.optmization_weights['decade_proportion']*abs(decade_proportion - proportion)*1000
                
                fitness_score += decade_score


        # Calculate the fitness score based on the maximum number of songs per artist in the setlist
        if setlist_songs_per_artist.max() > self.default_optimization_parameters.max_songs_per_artist:
            max_songs_per_artist_score = 1-abs(setlist_songs_per_artist.max() - self.default_optimization_parameters.max_songs_per_artist)/self.default_optimization_parameters.max_songs_per_artist
            print(f"max songs per artist score: {abs(self.optmization_weights['max_songs_per_artist']*max_songs_per_artist_score)}") if debug else None
            fitness_score += abs(self.optmization_weights['max_songs_per_artist']*max_songs_per_artist_score)

        # Calculate the fitness score based on the target features of the setlist
        for feature, target_value in self.default_optimization_parameters.target_features.items():
            feature_score = 1-abs(setlist_target_features.get(feature, 0) - target_value)/target_value
            print(f"feature {feature} score: {abs(self.optmization_weights['target_features']*feature_score)}") if debug else None
            fitness_score += abs(self.optmization_weights['target_features']*feature_score)

        # Check if the playlist has any repeated songs
        if len(set(current_setlist['id'])) < len(current_setlist):
            print(f"repeated songs score: {1e6*len(current_setlist) - len(set(current_setlist['id']))}") if debug else None
            fitness_score += 1e6*len(current_setlist) - len(set(current_setlist['id']))
        
        # ensure the fitness score is always positive
        fitness_score = max(0, fitness_score)
        

        return fitness_score,
    
    def __initate_toolbox(self)->None:
        logger.info('Initializing genetic algorithm toolbox')
        # Define the genetic algorithm functions
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        toolbox = base.Toolbox()
        toolbox.register("individual", tools.initIterate, creator.Individual, self.create_individual)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        toolbox.register("evaluate", self.fitness_function)
        toolbox.register("mate", self.__cxTwoPoint)
        toolbox.register("mutate", self.__mutateRandomSong, indpb=0.05)
        toolbox.register("select", tools.selTournament, tournsize=5)

        self.toolbox= toolbox

    def load_playlist(self, playlist: pd.DataFrame) -> None:
        self.playlist = playlist

    def remove_duplicates(self, individual:list|tuple)->tuple:
        if type(individual) == tuple:
            individual = list(individual[0])
        current_setlist = self.playlist.iloc[individual]

        repeated_songs = current_setlist[current_setlist.duplicated(subset='id')]

        if repeated_songs.empty:
            return individual
        
        for song in repeated_songs['id']:
            repeated_song_genre = current_setlist[current_setlist['id'] == song]['genre'].values[0]
            repeated_song_country = current_setlist[current_setlist['id'] == song]['country'].values[0]
            repeated_song_decade = current_setlist[current_setlist['id'] == song]['decade'].values[0]

            repeated_song_index = current_setlist[current_setlist['id'] == song].index[0]
            individual.remove(repeated_song_index)
            available_songs:pd.DataFrame = self.playlist[
                (self.playlist['genre'] == repeated_song_genre) &
                (self.playlist['country'] == repeated_song_country) &
                (self.playlist['decade'] == repeated_song_decade) &
                (~self.playlist.index.isin(individual))
            ]
            if available_songs.empty:
                available_songs = self.playlist[~self.playlist.index.isin(individual)]
            new_song = random.choice(available_songs.index.to_list())
            individual.append(new_song)

        return individual,
    
    def __mutateRandomSong(self,individual:list[list], indpb):
        size = len(individual)
        available_songs = self.playlist[~self.playlist.index.isin(individual)]
        for i in range(size):
            if random.random() < indpb:
                
                new_song = random.choice(available_songs.index.to_list())
                individual[i] = new_song
        
        individual = self.remove_duplicates(individual)
        individual = self.__check_for_missing_features(individual)

        return individual,

    def __cxTwoPoint(self,ind1:dict, ind2:dict):
        size = min(len(ind1), len(ind2))
        cxpoint1 = random.randint(1, size)
        cxpoint2 = random.randint(1, size - 1)
        if cxpoint2 >= cxpoint1:
            cxpoint2 += 1
        else:  # Swap the two cx points
            cxpoint1, cxpoint2 = cxpoint2, cxpoint1

        ind1[cxpoint1:cxpoint2], ind2[cxpoint1:cxpoint2] \
            = ind2[cxpoint1:cxpoint2], ind1[cxpoint1:cxpoint2]

        ind1 = self.__check_for_missing_features(ind1)
        ind1 = self.remove_duplicates(ind1)
        ind2 = self.__check_for_missing_features(ind2)
        ind2 = self.remove_duplicates(ind2)

        return ind1, ind2



    # Define the initial population
    def create_individual(self):
        return random.sample(self.playlist.index.to_list(), self.setlist_size)

    # Implement the main genetic algorithm loop
    def run_ga(self):
        logger.info('Running genetic algorithm')
        pop = self.toolbox.population(n=100)
        CXPB, MUTPB, NGEN = 0.4, 0.07, 210

        # Evaluate the entire population
        logger.info('Evaluating initial population')
        fitnesses = list(map(self.toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        for g in range(NGEN):
            # Select the next generation individuals
            logger.info(f'Running generation {g}')
            offspring = self.toolbox.select(pop, len(pop))
            # Clone the selected individuals
            offspring = list(map(self.toolbox.clone, offspring))

            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                if random.random() < MUTPB:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # The population is entirely replaced by the offspring
            logger.info(f'Generation {g} completed')
            pop[:] = offspring

        # Find the best individual in the population after the genetic algorithm is complete
        logger.info('Genetic algorithm complete. Finding best individual')
        result = max(pop, key=self.toolbox.evaluate)
        return result
    
    def __check_for_missing_features(self, individual:list|tuple)->tuple:
        if type(individual) == tuple:
            individual = list(individual[0])
        current_setlist = self.playlist.iloc[individual]

        genres_to_check = {genre: proportion for genre, proportion in self.default_optimization_parameters.genre_proportion.items() if proportion > 0}
        missing_genres = set(genres_to_check.keys()) - set(current_setlist['genre'].unique())
        
        if missing_genres:
            current_genres = current_setlist['genre'].value_counts()
            most_frequent_genre = current_genres.idxmax()
            songs_to_remove = current_setlist[current_setlist['genre'] == most_frequent_genre].index.to_list()
            available_songs:pd.DataFrame = self.playlist[
            (self.playlist['genre'].isin(missing_genres)) &
            (~self.playlist.index.isin(individual))
            ]
            if available_songs.empty:
                available_songs = self.playlist[~self.playlist.index.isin(individual)]
            song_to_remove = random.choice(songs_to_remove)
            individual.remove(song_to_remove)
            new_song = random.choice(available_songs.index.to_list())
            individual.append(new_song)
        
        countries_to_check = {country: proportion for country, proportion in self.default_optimization_parameters.country_proportion.items() if proportion > 0}
        missing_countries = set(countries_to_check.keys()) - set(current_setlist['country'].unique())

        if missing_countries:
            current_countries = current_setlist['country'].value_counts()
            most_frequent_country = current_countries.idxmax()
            songs_to_remove = current_setlist[current_setlist['country'] == most_frequent_country].index.to_list()
            song_to_remove = random.choice(songs_to_remove)
            individual.remove(song_to_remove)
            available_songs:pd.DataFrame = self.playlist[
            (self.playlist['country'].isin(missing_countries)) &
            (~self.playlist.index.isin(individual))
            ]
            if available_songs.empty:
                available_songs = self.playlist[~self.playlist.index.isin(individual)]
            new_song = random.choice(available_songs.index.to_list())
            individual.append(new_song)

        decades_to_check = {decade: proportion for decade, proportion in self.default_optimization_parameters.decade_proportion.items() if proportion > 0}
        missing_decades = set(decades_to_check.keys()) - set(current_setlist['decade'].unique())

        if missing_decades:
            current_decades = current_setlist['decade'].value_counts()
            most_frequent_decade = current_decades.idxmax()
            songs_to_remove = current_setlist[current_setlist['decade'] == most_frequent_decade].index.to_list()
            song_to_remove = random.choice(songs_to_remove)
            individual.remove(song_to_remove)
            available_songs:pd.DataFrame = self.playlist[
            (self.playlist['decade'].isin(missing_decades)) &
            (~self.playlist.index.isin(individual))
            ]
            if available_songs.empty:
                available_songs = self.playlist[~self.playlist.index.isin(individual)]
            new_song = random.choice(available_songs.index.to_list())
            individual.append(new_song)

        return individual,
        
