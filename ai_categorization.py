
from sqlalchemy import create_engine
from datamodels import ConfigFile
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from dotenv import load_dotenv
import pandas as pd
import json
import os

load_dotenv(override=True)

class song_features(BaseModel):
    name: str = Field(description="Name of the song")
    artists: str = Field(description="Artists of the song")
    genre: str = Field(description="Genre of the song. Must be ONLY ONE OF THESE: 'Rock', 'Pop' or 'Metal'")
    country: str = Field(description="Country of the song. Must be ONLY ONE OF THESE: 'BR' or 'International'")
    decade: str = Field(description="Decade of the song. Must be ONLY ONE OF THESE: '90s or before', '00s' or '10s or later'")


class AIChatCategorization():
    def __init__(self):
        db_path = os.getenv('db_url')
        config_file_path = os.getenv('config_file_path')

        self.engine = create_engine(db_path)
        with open(config_file_path) as f:
            self.config = json.load(f)

        self.config = ConfigFile(**self.config)

        self.prompt_templates_path = self.config.AI_configurations.prompt_templates_filepaths
        self.categories = self.config.AI_configurations.categories

        self.llm = ChatOpenAI(model=self.config.AI_configurations.model)
        
    def get_categorization(self, playlist_df:pd.DataFrame, features_columns: list[str], categories_names:list[str]=['genre', 'country', 'decade'])->pd.DataFrame:
        
        playlist_df[categories_names] = None
        
        categorization_prompt_file = self.prompt_templates_path["categorization"]
        with open(categorization_prompt_file) as f:
            categorization_prompt = f.read()

        parser = JsonOutputParser(pydantic_object=song_features)
        prompt = PromptTemplate(
            template=categorization_prompt,
            input_variables=["features", "categories"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt | self.llm | parser

        chunk_size = 30
        data_categories = pd.DataFrame()
        for i in range(0, len(playlist_df), chunk_size):
            chunk = playlist_df[i:i+chunk_size]
            features: dict = chunk[chunk[categories_names].isnull().all(axis=1)][features_columns].to_dict(orient='records')
            logger.info("Categorizing songs with OpenAI LLM")
            response = chain.invoke({"features": features, "categories": self.categories})
            data_categories = pd.concat([data_categories,pd.DataFrame(response)],ignore_index=True)
            logger.info(f"{i+chunk_size}/{len(playlist_df)} songs categorized. current response length: {len(data_categories)}")
        
        playlist_df.update(data_categories)
        return playlist_df



        
        
