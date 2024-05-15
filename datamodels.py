from pydantic import BaseModel

class AIConfigurations(BaseModel):
    model: str
    prompt_templates_filepaths: dict
    categories: dict

class DefaultOptimizationParameters(BaseModel):
    max_duration: int
    genre_proportion: dict
    country_proportion: dict
    decade_proportion: dict
    max_songs_per_artist: int
    target_features: dict
    minimum_popularity: int

class General(BaseModel):
    default_playlist_id: str
    default_optimization_parameters: DefaultOptimizationParameters

class ConfigFile(BaseModel):
    AI_configurations: AIConfigurations
    general: General


class configFile(BaseModel):
    AI_configurations: AIConfigurations
    general: General