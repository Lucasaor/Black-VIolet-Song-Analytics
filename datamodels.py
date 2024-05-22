from pydantic import BaseModel

class AIConfigurations(BaseModel):
    model: str
    prompt_templates_filepaths: dict[str, str]
    categories: dict[str, list[str]]

class DefaultOptimizationParameters(BaseModel):
    max_duration: int
    genre_proportion: dict[str, float]
    country_proportion: dict[str, float]
    decade_proportion: dict[str, float]
    max_songs_per_artist: int
    target_features: dict[str, float]
    minimum_popularity: int

class General(BaseModel):
    setlist_size: int
    default_playlist_id: str
    default_optimization_parameters: DefaultOptimizationParameters
    Optmization_weights: dict[str, float]

class ConfigFile(BaseModel):
    AI_configurations: AIConfigurations
    general: General
