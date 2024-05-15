import os
import itertools
import aiohttp
from loguru import logger


class SpotifyApiManager():
    def __init__(self):
        self.client_id = os.environ.get('client_id')
        self.client_secret = os.environ.get('client_secret')
        self.api_base_url = os.environ.get('api_base_url')
        self.api_auth_url = os.environ.get('api_auth_url')
        self.pitch_class_notation_dict = {
            -1: None,
            0: 'C',
            1: 'C#',
            2: 'D',
            3: 'D#',
            4: 'E',
            5: 'F',
            6: 'F#',
            7: 'G',
            8: 'G#',
            9: 'A',
            10: 'A#',
            11: 'B'
        }
        self.mode_dict = {
            0: 'Minor',
            1: 'Major'
        }
        self.token = None

    async def get_token(self)->None:
        if self.token is None:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_auth_url,
                    data={
                        'grant_type': 'client_credentials',
                        'client_id': self.client_id,
                        'client_secret': self.client_secret
                    }
                ) as response:
                    response_json = await response.json()
                    self.token = response_json['access_token']

    async def get_playlist_tracks(self, playlist_id:str, country:str='BR')->list:
        track_list = []
        await self.get_token()
        finished_getting_tracks = False
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{self.api_base_url}/playlists/{playlist_id}/tracks?country={country}',
                headers={
                    'Authorization': f'Bearer {self.token}'
                }
            ) as response:
                response_json = await response.json()
                
                if 'items' in response_json:
                    for item in response_json['items']:
                        track = item['track']
                        track_list.append(
                            {
                            'id': track['id'],
                            'name': track['name'],
                            'artist_data': track['artists'],
                            'artists': ','.join([artist['name'] for artist in track['artists']]),
                            'album': track['album']['name'],
                            'popularity': track['popularity'],
                            'preview_url': track['preview_url'],
                            'release_date': track['album']['release_date'],
                            'release_date_precision': track['album']['release_date_precision'],
                            'duration_ms': track['duration_ms']
                        }
                        )
                    
                if response_json['next'] is None:
                    finished_getting_tracks = True
                while not finished_getting_tracks:
                    async with session.get(
                        response_json['next'],
                        headers={
                            'Authorization': f'Bearer {self.token}'
                        }
                    ) as response:
                        response_json = await response.json()
                        if 'items' in response_json:
                            for item in response_json['items']:
                                track = item['track']
                                track_list.append(
                                    {   
                                        'id': track['id'],
                                        'name': track['name'],
                                        'artist_data': track['artists'],
                                        'artists': ','.join([artist['name'] for artist in track['artists']]),
                                        'album': track['album']['name'],
                                        'popularity': track['popularity'],
                                        'preview_url': track['preview_url'],
                                        'release_date': track['album']['release_date'],
                                        'release_date_precision': track['album']['release_date_precision'],
                                        'duration_ms': track['duration_ms']
                                    }
                                )
                        if response_json['next'] is None:
                            finished_getting_tracks = True
        return track_list

    async def get_artist_genres(self, artist_id:str)->list:
        genre_list = []
        await self.get_token()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{self.api_base_url}/artists/{artist_id}',
                headers={
                    'Authorization': f'Bearer {self.token}'
                }
            ) as response:
                response_json = await response.json()
                if 'genres' in response_json:
                    genre_list = response_json['genres']
        return genre_list
    

    async def create_artist_genre_dict(self, playlist:list[str])->dict:
        artists_data = [playlist[track]['artist_data'] for track in range(len(playlist))]
        artists_data_flat = list(itertools.chain.from_iterable(artists_data))
        artists_id = set([artist['id'] for artist in artists_data_flat])
        genres_per_artist = [await self.get_artist_genres(artist_id) for artist_id in artists_id]
        return dict(zip(artists_id, genres_per_artist))
    
    async def get_audio_features(self, playlist:list[dict])->list[dict]:
        await self.get_token()
        async with aiohttp.ClientSession() as session:
            for track in playlist:
                async with session.get(
                f'{self.api_base_url}/audio-features/{track["id"]}',
                headers={
                    'Authorization': f'Bearer {self.token}'
                }
            ) as response:
                    feature = await response.json()

                track['danceability'] = feature.get('danceability')
                track['energy'] = feature.get('energy')
                track['key_code'] = feature.get('key')
                track['key'] = self.pitch_class_notation_dict.get(feature.get('key'))
                track['loudness'] = feature.get('loudness')
                track['mode_code'] = feature.get('mode')
                track['mode'] = self.mode_dict.get(feature.get('mode'))
                track['speechiness'] = feature.get('speechiness')
                track['acousticness'] = feature.get('acousticness')
                track['valence'] = feature.get('valence')
                track['tempo'] = feature.get('tempo')
                track['time_signature'] = feature.get('time_signature')
        return playlist

    @staticmethod
    def apply_genre_to_playlist(playlist:list[dict], artist_genre_dict:dict)->list[dict]:
        for track in playlist:
            track_genres = []
            for artist in track['artist_data']:
                if artist['id'] in artist_genre_dict:
                    track_genres.extend(artist_genre_dict[artist['id']])
            track_genres = list(set(track_genres))
            track['genres'] = ','.join(track_genres)
        return playlist
    
