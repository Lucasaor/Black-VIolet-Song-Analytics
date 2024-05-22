from sqlalchemy import create_engine
from ai_categorization import AIChatCategorization
from playlist_optmizer import PlaylistOptimizer
from loguru import logger
import pandas as pd


def main():
    logger.info('Starting the playlist optimization process')
    engine = create_engine('sqlite:///data/data.db', echo=False)

    logger.info('Loading the playlist data')
    playlist = pd.read_sql('playlist', con=engine)

    playlist_optimizer = PlaylistOptimizer()

    logger.info('Running the genetic algorithm')
    playlist_optimizer.load_playlist(playlist)


    result = playlist_optimizer.run_ga()

    result = playlist_optimizer.remove_duplicates(result)

    result_df:pd.DataFrame = playlist.loc[result]

    logger.info('Saving the optimized playlist')
    result_df.to_sql('current_playlist', con=engine, if_exists='replace', index=False)
    logger.info('Optimized playlist:')
    print(result_df[['name', 'artists']])

    setlist_features = playlist_optimizer.calculate_setlist_features(result_df)
    logger.info('Setlist features:')
    print(setlist_features)

    score = playlist_optimizer.fitness_function(result)
    logger.info('Setlist score:')
    print(score)


if __name__ == '__main__':
    main()