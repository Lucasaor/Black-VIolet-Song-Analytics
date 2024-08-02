from song_analytics import SongAnalytics
from datamodels import ConfigFile
from chart_generator import ChartGenerator
import json
import pandas as pd
import streamlit as st
import asyncio

setlist_features_evaluated = False

def main():
    global setlist_features_evaluated
    logo_path = 'logo7.png'
    st.image(logo_path, use_column_width=True)
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


    st.write("## Menu de carregamento de playlists")
    st.write("Carregar novos dados de playlist do Spotify ou do banco de dados")
    playlist_id = st.text_input("ID ou URL da playlist", value=config.general.default_playlist_id)
    if playlist_id.startswith("https://open.spotify.com/playlist/"):
        playlist_id = playlist_id.split('/')[-1]
        playlist_id = playlist_id.split('?')[0]
    embed_url = f"https://embed.spotify.com/?uri=spotify:playlist:{playlist_id}"
    iframe_code = f'<iframe src="{embed_url}" width="704" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
    st.markdown(iframe_code, unsafe_allow_html=True)
    left, right = st.columns(2)
    if left.button("Carregar playlist do spotify",use_container_width=True):
        asyncio.run(song_analytics.load_playlist_from_spotify(playlist_id))
        st.success("Playlist carregada com sucesso!")
        
        setlist_features_evaluated = False
    if right.button("Carregar playlist do banco de dados",use_container_width=True):
        asyncio.run(song_analytics.load_playlist_from_db(playlist_id))
        st.success("Playlist carregada com sucesso!")
        setlist_features_evaluated = False

    st.write("Use a opção de análise de playlist após carregá-la o Spotify para adicionar as categorias de música")
    if st.button("Analisar playlist com IA"):
        song_analytics.categorize_playlist_with_ai(playlist_id)
        st.success("Playlist categorizada com sucesso!")
        setlist_features_evaluated = False

    st.write("Use o botão abaixo para gerar um setlist a partir da playlist carregada")
    setlist_name = st.text_input("Nome do setlist", value="Setlist")
    setlist_description = st.text_input("Descrição do setlist", value="Setlist gerado automaticamente")
    
    if st.button("Construir setlist otimizado"):
        song_analytics.build_setlist_from_playlist(setlist_name, setlist_description)
        st.write("Setlist gerado com sucesso!")
        setlist_df:pd.DataFrame = song_analytics.current_playlist
        st.dataframe(setlist_df)
    
    st.write("Carregar setlist já existente")
    if st.button("Carregar último setlist do banco de dados"):
        song_analytics.load_current_setlist_from_db()
        st.success("Setlist carregado com sucesso!")
        setlist_df:pd.DataFrame = song_analytics.current_playlist
        st.dataframe(setlist_df)
        setlist_features_evaluated = False

    st.write("## Avaliação de setlist")

    if st.button("Avaliar setlist"):
        setlist_features_evaluated =True
        if song_analytics.current_playlist is None:
            st.warning("Carregue uma playlist antes de avaliá-la!")
        else:
            setlist_features,score = song_analytics.evaluate_setlist()
            score = score[0]
            st.success("Setlist avaliado com sucesso!")

    if setlist_features_evaluated:
        chart_generator = ChartGenerator(config)
        st.write("## Características do setlist")

        left, right = st.columns(2)
        
        with left:
            duration = setlist_features['total_duration_minutes']
            target_duration = config.general.default_optimization_parameters.max_duration
            if abs(target_duration - duration)/target_duration < 0.05:
                duration_text = "Boa"
            elif abs(target_duration - duration)/target_duration < 0.1:
                duration_text = "Regular"
            else:
                duration_text = "-Ruim"
            st.metric("Duração do setlist", round(duration,2), duration_text)

            st.write("Proporção de Gênero do Setlist")
            fig = chart_generator.generate_bar_chart_genre_proportion(setlist_features['setlist_genre_proportion'])
            st.plotly_chart(fig, use_container_width=True)

            st.write("Proporção de Países do Setlist")
            fig = chart_generator.generate_bar_chart_country_proportion(setlist_features['setlist_country_proportion'])
            st.plotly_chart(fig, use_container_width=True)

            if score < 5:
                score_text = "Boa"
            elif score < 10:
                score_text = "Regular"
            else:
                score_text = "-Ruim"
            
            

            
        with right:
            popularity = setlist_features['setlist_popularity']
            target_popularity = config.general.default_optimization_parameters.minimum_popularity
            if abs(target_popularity - popularity)/target_popularity < 0.05:
                popularity_text = "Boa"
            elif abs(target_popularity - popularity)/target_popularity < 0.1:
                popularity_text = "Regular"
            else:
                popularity_text = "-Ruim"


            st.metric("Popularidade do setlist", round(popularity,2), popularity_text)

            st.write("Proporção de Décadas do Setlist")
            fig = chart_generator.generate_bar_chart_decade_proportion(setlist_features['setlist_decade_proportion'])
            st.plotly_chart(fig, use_container_width=True)
            
            left_2, right_2 = st.columns(2)
            counter = 0
            for feature,value in setlist_features['setlist_target_features'].items():
                if counter //2 == 0:
                    with left_2:
                        st.metric(f"{feature.capitalize()} do setlist", round(value,2), None)
                else:
                    with right_2:
                        st.metric(f"{feature.capitalize()} do setlist", round(value,2), None)
                counter += 1
            st.metric("Pontuação do setlist", round(score,2), score_text)            

if __name__ == '__main__':
    main()