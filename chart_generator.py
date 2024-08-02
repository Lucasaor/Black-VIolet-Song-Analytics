import plotly.graph_objects as go
from datamodels import ConfigFile
import plotly.express as px
import pandas as pd

class ChartGenerator():
    def __init__(self,config:ConfigFile):
        self.config = config

    def generate_gauge_total_minutes(self, actual_duration:float)->go.Figure:
        target_duration = self.config.general.default_optimization_parameters.max_duration

        fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = actual_duration,
        title = {'text': "Duração do Setlist"},
        gauge = {
            'axis': {'range': [0, target_duration * 1.2]},
            'bar': {'color': "darkblue",'thickness': 0.3},
            'steps': [
                {'range': [0, target_duration * 0.9], 'color': "lightgray"},
                {'range': [target_duration * 0.9, target_duration], 'color': "green"},
                {'range': [target_duration, target_duration * 1.1], 'color': "lightgreen"},
                {'range': [target_duration * 1.1, target_duration * 1.2], 'color': "orange"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': target_duration
            }
        }
    ))

        fig.update_layout(height=400, margin={'t':50, 'b':0, 'l':0, 'r':0})
        return fig

    def generate_gauge_popularity(self, actual_popularity:float)->go.Figure:
        target_popularity = self.config.general.default_optimization_parameters.minimum_popularity

        fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = actual_popularity,
        title = {'text': "Popularidade do Setlist"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue",'thickness': 0.3},
            'steps': [
                {'range': [0, target_popularity * 0.95], 'color': "lightgray"},
                {'range': [target_popularity * 0.95, target_popularity], 'color': "lightgreen"},
                {'range': [target_popularity, target_popularity * 1.05], 'color': "lightgreen"},
                {'range': [target_popularity * 1.05, 100], 'color': "green"}
                
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': target_popularity
                    }
                }
            ))

        fig.update_layout(height=400, margin={'t':50, 'b':0, 'l':0, 'r':0})
        return fig
    
    def generate_bar_chart_genre_proportion(self, genre_proportion:dict[str,float])->go.Figure:
        target_genre_proportion = self.config.general.default_optimization_parameters.genre_proportion
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[x.capitalize() for x in genre_proportion.keys()], y=list(genre_proportion.values()), name='Proporção atual'))
        fig.add_trace(go.Bar(x=[x.capitalize() for x in target_genre_proportion.keys()], y=list(target_genre_proportion.values()), name='Proporção desejada'))

        fig.update_layout(barmode='group', height=400, margin={'t':50, 'b':0, 'l':0, 'r':0})
        return fig
    
    def generate_bar_chart_country_proportion(self, country_proportion:dict[str,float])->go.Figure:
        target_country_proportion = self.config.general.default_optimization_parameters.country_proportion
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[x.capitalize() for x in country_proportion.keys()], y=list(country_proportion.values()), name='Proporção atual'))
        fig.add_trace(go.Bar(x=[x.capitalize() for x in target_country_proportion.keys()], y=list(target_country_proportion.values()), name='Proporção desejada'))

        fig.update_layout(barmode='group', height=400, margin={'t':50, 'b':0, 'l':0, 'r':0})
        return fig
    
    def generate_bar_chart_decade_proportion(self, decade_proportion:dict[str,float])->go.Figure:
        target_decade_proportion = self.config.general.default_optimization_parameters.decade_proportion
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[x.capitalize() for x in decade_proportion.keys()], y=list(decade_proportion.values()), name='Proporção atual'))
        fig.add_trace(go.Bar(x=[x.capitalize() for x in target_decade_proportion.keys()], y=list(target_decade_proportion.values()), name='Proporção desejada'))

        fig.update_layout(barmode='group', height=400, margin={'t':50, 'b':0, 'l':0, 'r':0})
        return fig
    
    def generate_bar_chart_target_features(self, target_features:dict)->go.Figure:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=list(target_features.keys()), y=list(target_features.values())))

        fig.update_layout(height=400, margin={'t':50, 'b':0, 'l':0, 'r':0})
        return fig
    
    def generate_card_setlist_score(self, score:float)->go.Figure:
        if score < 5:
            text = "Boa"
            color = "green"
        elif score < 10:
            text = "Regular"
            color = "yellow"
        else:
            text = "Ruim"
            color = "red"
        
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode = "number",
            value = score,
            title = {'text': "Pontuação do Setlist"},
            number = {'suffix': "/10"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'visible': False},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 5], 'color': 'green'},
                    {'range': [5, 10], 'color': 'yellow'},
                    {'range': [10, 15], 'color': 'red'}
                ],
                'threshold': {
                    'line': {'color': 'black', 'width': 2},
                    'thickness': 0.75,
                    'value': score
                }
            }
        ))

        fig.update_layout(height=400, margin={'t':50, 'b':0, 'l':0, 'r':0})
        return fig
    
    def generate_card_max_songs_per_artist(self,actual_songs_per_artist:int)->go.Figure:
        max_songs_per_artist = self.config.general.default_optimization_parameters.max_songs_per_artist
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode = "number+delta",
            value = actual_songs_per_artist,
            title = {'text': "Máximo de Músicas por Artista"},
            number = {'suffix': f"/{max_songs_per_artist}"},
            delta = {'reference': max_songs_per_artist, 'position': "top"},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))

        fig.update_layout(height=400, margin={'t':50, 'b':0, 'l':0, 'r':0})
        return fig