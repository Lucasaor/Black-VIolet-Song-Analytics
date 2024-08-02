from sqlalchemy import create_engine,text
from spotify_api_manager import SpotifyApiManager
from ai_categorization import AIChatCategorization
from playlist_optmizer import PlaylistOptimizer
from playlist_clusterer import PlaylistClusterer
from dotenv import load_dotenv
from loguru import logger
import pandas as pd
import asyncio
import os

load_dotenv(override=True)

class SongAnalytics:
    def __init__(self):
        self.spotify_api_manager = SpotifyApiManager()
        self.ai_categorization = AIChatCategorization()
        self.playlist_optimizer = PlaylistOptimizer()
        self.playlist_clusterer = PlaylistClusterer()
        self.current_playlist = pd.DataFrame()
        db_url = os.environ.get('db_url')
        self.engine = create_engine(db_url, echo=False)

    async def load_playlist_from_spotify(self, playlist_id:str, country:str='BR')->pd.DataFrame:
        self.playlist_id = playlist_id
        await self.spotify_api_manager.get_token()
        track_list = await self.spotify_api_manager.get_playlist_tracks(playlist_id, country)

        genres_per_artist = await self.spotify_api_manager.create_artist_genre_dict(track_list)
        track_list = self.spotify_api_manager.apply_genre_to_playlist(track_list, genres_per_artist)

        # get the audio features of the tracks
        track_list = await self.spotify_api_manager.get_audio_features(track_list)

        self.current_playlist = pd.DataFrame(track_list)
        self.current_playlist.drop(columns=['artist_data','key_code','mode_code'], inplace=True)
        self.current_playlist['playlist_id'] = playlist_id
        with self.engine.connect() as connection:
            connection.execute(text(f"DELETE FROM playlist WHERE playlist_id = '{playlist_id}'"))
            connection.commit()

        self.current_playlist.to_sql('playlist', con=self.engine, if_exists='append', index=False)
        self.current_playlist.to_sql('current_playlist', con=self.engine, if_exists='replace', index=False)
        return self.current_playlist
    
    def get_current_playlist(self)->pd.DataFrame:
        return self.current_playlist

    def categorize_playlist_with_ai(self,playlist_id:str)->None:
        logger.info(f'Categorizing the playlist {playlist_id} with AI')
        playlist_table = pd.read_sql("playlist", con=self.engine)
        playlist_db_with_no_duplicates = playlist_table.drop_duplicates(subset=['id'])
        playlist_db_with_no_duplicates = playlist_db_with_no_duplicates.dropna(subset=['genre'])
        playlist_table = playlist_table.merge(playlist_db_with_no_duplicates[['id','genre','decade','country']], on='id', how='left', suffixes=('', '_db'))
        for column in ['genre','decade','country']:
            playlist_table[column] = playlist_table[column].fillna(playlist_table[column+'_db'])
            playlist_table = playlist_table.drop(columns=[column+'_db'])
        mask = playlist_table['playlist_id'] == playlist_id
        self.current_playlist = playlist_table[mask]
        if self.current_playlist.empty:
            raise ValueError(f'Playlist with id {playlist_id} not found in db')
        elif self.current_playlist['genre'].notnull().all():
            logger.info('Playlist already categorized')
        else:
            self.current_playlist = self.ai_categorization.get_categorization(self.current_playlist, ['id','name', 'artists', 'genres','album','release_date'])
            logger.info('Saving the categorized playlist')
        with self.engine.connect() as connection:
            connection.execute(text(f"DELETE FROM playlist WHERE playlist_id = '{playlist_id}'"))
            connection.commit()
        self.current_playlist.to_sql('playlist', con=self.engine, if_exists='append', index=False)
        self.current_playlist.to_sql('current_playlist', con=self.engine, if_exists='replace', index=False)

    def build_setlist_from_playlist(self,result_playlist_name:str, result_playlist_description:str)->dict:
        result_dict = {}
        logger.info('Starting the playlist optimization process')

        logger.info('Loading the playlist data')
        playlist = pd.read_sql('playlist', con=self.engine)

        logger.info('Running the genetic algorithm')

        playlist_optimizer = self.playlist_optimizer
        playlist_clusterer = self.playlist_clusterer
        
        playlist_optimizer.load_playlist(playlist)


        result = playlist_optimizer.run_ga()

        result = playlist_optimizer.remove_duplicates(result)

        result_df:pd.DataFrame = playlist.loc[result]

        logger.info("adding cluster column")
        result_df = playlist_clusterer.cluster_pipeline(result_df)

        logger.info('Saving the optimized playlist')
        result_df.to_sql('current_playlist', con=self.engine, if_exists='replace', index=False)
        logger.info('Optimized playlist:')
        print(result_df[['name', 'artists']])
        result_dict['playlist'] = result_df

        setlist_features = playlist_optimizer.calculate_setlist_features(result_df)
        logger.info('Setlist features:')
        print(setlist_features)
        result_dict['setlist_features'] = setlist_features

        score = playlist_optimizer.fitness_function(result)
        logger.info('Setlist score:')
        print(score)
        result_dict['score'] = score
        return result_dict

    def evaluate_setlist(self)->tuple[dict, float]:
        if self.current_playlist.empty:
            self.current_playlist = pd.read_sql('current_playlist', con=self.engine)
        playlist_optimizer = self.playlist_optimizer
        playlist_optimizer.load_playlist(self.current_playlist)
        setlist_features = playlist_optimizer.calculate_setlist_features(self.current_playlist)
        score = playlist_optimizer.fitness_function(self.current_playlist.index,debug=True)

        return setlist_features, score


    def categorize_and_run_song_analytcs(self, playlist_id:str, country:str='BR')->None:
        asyncio.run(self.load_playlist_from_spotify(playlist_id, country))
        self.categorize_playlist_with_ai()
        self.build_setlist_from_playlist()

    async def create_setlist_playlist(self, playlist_name:str, playlist_description:str)->None:
        current_playlist = pd.read_sql('current_playlist', con=self.engine)
        playlist_tracks = current_playlist['id'].tolist()
        await self.spotify_api_manager.get_token()
        playlist_id = await self.spotify_api_manager.create_setlist_playlist(playlist_name, playlist_description, playlist_tracks)
        return playlist_id

    async def update_setlist_playlist(self, playlist_id:str)->None:
        current_playlist = pd.read_sql('current_playlist', con=self.engine)
        playlist_tracks = current_playlist['id'].tolist()
        await self.spotify_api_manager.get_token()
        await self.spotify_api_manager.update_setlist_playlist(playlist_id, playlist_tracks)

    async def load_playlist_from_db(self, playlist_id:str)->pd.DataFrame:
        self.current_playlist = pd.read_sql(f"SELECT * FROM playlist WHERE playlist_id = '{playlist_id}'", con=self.engine)
        if self.current_playlist.empty:
            await self.load_playlist_from_spotify(playlist_id)
            return self.current_playlist
        self.current_playlist.to_sql('current_playlist', con=self.engine, if_exists='replace', index=False)
        return self.current_playlist
    
    def load_current_setlist_from_db(self)->pd.DataFrame:
        self.current_playlist = pd.read_sql('current_playlist', con=self.engine)
        return self.current_playlist