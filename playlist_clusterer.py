import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from loguru import logger

class PlaylistClusterer:
    def __init__(self, n_clusters=5):
        self.n_clusters = n_clusters

        self.numerical_features = ['danceability', 'energy', 'key', 'loudness', 'speechiness',
                                   'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo',
                                   'time_signature']
        self.categorical_features = ['mode','genre', 'country', 'decade']

        self.pitch_notation = {
                            None: -1,
                            'C': 0,
                            'C#': 1,
                            'D': 2,
                            'D#': 3,
                            'E': 4,
                            'F': 5,
                            'F#': 6,
                            'G': 7,
                            'G#': 8,
                            'A': 9,
                            'A#': 10,
                            'B': 11
                        }

        self.__initiate_pipeline()

    
    def __initiate_pipeline(self):
        preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), self.numerical_features),
            ('cat', OneHotEncoder(), self.categorical_features)
        ])
        self.pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                        ('kmeans', KMeans(n_clusters=self.n_clusters))])
        
    
    def cluster_pipeline(self, df:pd.DataFrame)->pd.DataFrame:
        df['key'] = df['key'].map(self.pitch_notation)
        input_df = df[self.numerical_features + self.categorical_features]
        input_df = input_df.fillna(0.0)
        self.pipeline.fit(input_df)
        df['cluster'] = self.pipeline.predict(input_df)

        df = self.__update_cluster_centers(df)
        return df
        
    
    def __update_cluster_centers(self, df:pd.DataFrame):
        cluster_centers = self.pipeline.named_steps['kmeans'].cluster_centers_
        centroid_df = pd.DataFrame(cluster_centers)
        centroid_df = centroid_df.iloc[:,0:len(self.numerical_features)]
        centroid_df.columns = self.numerical_features
        fisrt_energy,second_energy = centroid_df.sort_values('energy',ascending=False).index[:2]
        fisrt_dance = centroid_df.drop([fisrt_energy,second_energy]).sort_values('danceability',ascending=False).index[0]
        other_1, other_2 = centroid_df.drop([fisrt_energy,second_energy,fisrt_dance]).index

        new_cluster_sequence = {
            fisrt_energy:0,
            other_1:1,
            fisrt_dance:2,
            other_2:3,
            second_energy:4
        }

        df['cluster'] = df['cluster'].map(new_cluster_sequence)
        df.sort_values('cluster',inplace=True)
        return df