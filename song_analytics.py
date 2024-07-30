from sqlalchemy import create_engine
from spotify_api_manager import SpotifyApiManager
from ai_categorization import AIChatCategorization
from playlist_optmizer import PlaylistOptimizer
from playlist_clusterer import PlaylistClusterer
from loguru import logger
import pandas as pd
import asyncio
import os

class SongAnalytics:
    def __init__(self):
        self.spotify_api_manager = SpotifyApiManager()
        self.ai_categorization = AIChatCategorization()
        self.playlist_optimizer = PlaylistOptimizer()
        self.playlist_clusterer = PlaylistClusterer()
        self.current_playlist = pd.DataFrame()
        db_url = os.environ.get('DATABASE_URL')
        self.engine = create_engine(db_url, echo=False)

    async def load_playlist_from_spotify(self, playlist_id:str, country:str='BR')->None:
        self.playlist_id = playlist_id
        await self.spotify_api_manager.get_token()
        track_list = await self.spotify_api_manager.get_playlist_tracks(playlist_id, country)

        genres_per_artist = await self.spotify_api_manager.apply_genre_to_playlist(track_list)
        track_list = self.spotify_api_manager.apply_genre_to_playlist(track_list, genres_per_artist)

        # get the audio features of the tracks
        track_list = await self.spotify_api_manager.get_audio_features(track_list)

        self.current_playlist = pd.DataFrame(track_list)
        self.current_playlist.to_sql('playlist', con=self.engine, if_exists='replace', index=False)
    
    def get_current_playlist(self)->pd.DataFrame:
        return self.current_playlist
    
    
    def categorize_playlist_with_ai(self)->None:
        self.current_playlist = self.ai_categorization.get_categorization(self.current_playlist, ['id','name', 'artists', 'genres','album','release_date'])
        self.current_playlist.to_sql('playlist', con=self.engine, if_exists='replace', index=False)

    def run_song_analytics():
        logger.info('Starting the playlist optimization process')
        engine = create_engine('sqlite:///data/data.db', echo=False)

        logger.info('Loading the playlist data')
        playlist = pd.read_sql('playlist', con=engine)

        logger.info('Running the genetic algorithm')

        playlist_optimizer = PlaylistOptimizer()
        playlist_clusterer = PlaylistClusterer()
        
        playlist_optimizer.load_playlist(playlist)


        result = playlist_optimizer.run_ga()

        result = playlist_optimizer.remove_duplicates(result)

        result_df:pd.DataFrame = playlist.loc[result]

        logger.info("adding cluster column")
        result_df = playlist_clusterer.cluster_pipeline(result_df)

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

    def categorize_and_run_song_analytcs(self, playlist_id:str, country:str='BR')->None:
        asyncio.run(self.load_playlist_from_spotify(playlist_id, country))
        self.categorize_playlist_with_ai()
        self.run_song_analytics()

