from pydantic import BaseSettings


class Settings(BaseSettings):
    api_key: str
    api_secret: str

    class Config:
        env_prefix = 'bf_'
        env_file = '.env'
        case_sensitive = False
