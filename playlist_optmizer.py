import pandas as pd
from datamodels import configFile
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

        self.config = configFile(**self.config)

        self.default_optimization_parameters = self.config.general.default_optimization_parameters
    
        self.__initate_toolbox()

    # Define the fitness function
    def fitness_function(self,individual):
        current_setlist = self.playlist.iloc[individual]
        total_duration_minutes = current_setlist['duration_ms'].sum()/1000
        
        setlist_popularity = current_setlist['popularity'].mean()

        setlist_genre_proportion = current_setlist['genre'].value_counts(normalize=True).to_dict()
        setlist_country_proportion = current_setlist['country'].value_counts(normalize=True).to_dict()
        setlist_decade_proportion = current_setlist['decade'].value_counts(normalize=True).to_dict()

        setlist_songs_per_artist = current_setlist['artists'].value_counts()

        setlist_target_features = current_setlist[['danceability', 'energy', 'loudness', 'valence']].mean().to_dict()


        pass
    def __initate_toolbox(self):
        logger.info('Initializing genetic algorithm toolbox')
        # Define the genetic algorithm functions
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        toolbox.register("individual", tools.initIterate, creator.Individual, self.create_individual)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        toolbox.register("evaluate", self.fitness_function)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
        toolbox.register("select", tools.selTournament, tournsize=3)

    def load_playlist(self, playlist: pd.DataFrame) -> None:
        self.playlist = playlist


    # Define the initial population
    def create_individual(dataframe):
        return random.sample(range(len(dataframe)), 30)

    # Implement the main genetic algorithm loop
    def run_ga(self):
        logger.info('Running genetic algorithm')
        pop = self.toolbox.population(n=50)
        CXPB, MUTPB, NGEN = 0.5, 0.2, 40

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