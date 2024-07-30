from sqlalchemy import create_engine
from song_analytics import SongAnalytics
from datamodels import ConfigFile
import json
from loguru import logger
import pandas as pd
import streamlit as st
import asyncio


def main():
    st.title('Black Violet Song Analytics')
    st.write('Este é o aplicativo de análise de setlists da banda Black Violet')

    # Load the config file
    config_file_path='config/config.json'
    with open(config_file_path) as f:
        config = json.load(f)
    config = ConfigFile(**config)
    
    song_analytics = SongAnalytics()


    # Create a menu to edit the "General" field in the config file
    with st.sidebar:
        st.write("# Configurações gerais")
        config.general.setlist_size = st.number_input("Número de músicas no setlist", value=config.general.setlist_size)
        config.general.default_optimization_parameters.max_duration = st.number_input("Duração máxima do setlist (em minutos)", value=config.general.default_optimization_parameters.max_duration)
        config.general.default_optimization_parameters.max_songs_per_artist = st.number_input("Número máximo de músicas por artista", value=config.general.default_optimization_parameters.max_songs_per_artist)
        config.general.default_optimization_parameters.minimum_popularity = st.slider("Popularidade mínima das músicas", min_value=0, max_value=100, value=config.general.default_optimization_parameters.minimum_popularity)

        st.write("## Proporção de gêneros")
        config.general.default_optimization_parameters.genre_proportion["rock"] = st.slider("Rock", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.genre_proportion["rock"])
        config.general.default_optimization_parameters.genre_proportion["pop"] = st.slider("Pop", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.genre_proportion["pop"])
        config.general.default_optimization_parameters.genre_proportion["metal"] = st.slider("Metal", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.genre_proportion["metal"])
        config.general.default_optimization_parameters.genre_proportion["other"] = st.slider("Outros gêneros", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.genre_proportion["other"])

        st.write("## Proporção de países")
        config.general.default_optimization_parameters.country_proportion["BR"] = st.slider("Nacional", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.country_proportion["BR"])
        config.general.default_optimization_parameters.country_proportion["international"] = st.slider("Internacional", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.country_proportion["international"])

        st.write("## Proporção de décadas")
        config.general.default_optimization_parameters.decade_proportion["90s"] = st.slider("Anos 90", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.decade_proportion["90s"])
        config.general.default_optimization_parameters.decade_proportion["00s"] = st.slider("Anos 2000", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.decade_proportion["00s"])
        config.general.default_optimization_parameters.decade_proportion["10s"] = st.slider("Anos 2010", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.decade_proportion["10s"])
        config.general.default_optimization_parameters.decade_proportion["other"] = st.slider("Outras décadas", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.decade_proportion["other"])

        st.write("## Características desejadas das músicas")
        config.general.default_optimization_parameters.target_features["danceability"] = st.slider("Dançante", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.target_features["danceability"])
        config.general.default_optimization_parameters.target_features["energy"] = st.slider("Energia", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.target_features["energy"])
        config.general.default_optimization_parameters.target_features["valence"] = st.slider("Valência", min_value=0.0, max_value=1.0, value=config.general.default_optimization_parameters.target_features["valence"])
        config.general.default_optimization_parameters.target_features["loudness"] = st.slider("Volume", min_value=-10.0, max_value=0.0, value=config.general.default_optimization_parameters.target_features["loudness"])

        st.write("## Pesos das características")
        config.general.Optmization_weights["max_duration"] = st.slider("Duração máxima", min_value=0.0, max_value=5.0, value=config.general.Optmization_weights["max_duration"])
        config.general.Optmization_weights["genre_proportion"] = st.slider("Proporção de gênero", min_value=0.0, max_value=5.0, value=config.general.Optmization_weights["genre_proportion"])
        config.general.Optmization_weights["country_proportion"] = st.slider("Proporção de país", min_value=0.0, max_value=5.0, value=config.general.Optmization_weights["country_proportion"])
        config.general.Optmization_weights["decade_proportion"] = st.slider("Proporção de década", min_value=0.0, max_value=5.0, value=config.general.Optmization_weights["decade_proportion"])
        config.general.Optmization_weights["max_songs_per_artist"] = st.slider("Máximo de músicas por artista", min_value=0.0, max_value=5.0, value=config.general.Optmization_weights["max_songs_per_artist"])
        config.general.Optmization_weights["minimum_popularity"] = st.slider("Popularidade mínima", min_value=0.0, max_value=5.0, value=config.general.Optmization_weights["minimum_popularity"])
        config.general.Optmization_weights["target_features"] = st.slider("Características desejadas", min_value=0.0, max_value=5.0, value=config.general.Optmization_weights["target_features"])

        if st.button("Exportar configurações"):
            with open(config_file_path, 'w') as f:
                json.dump(config.model_dump(), f, indent=4)
                st.write("Configurações exportadas com sucesso!")



if __name__ == '__main__':
    main()