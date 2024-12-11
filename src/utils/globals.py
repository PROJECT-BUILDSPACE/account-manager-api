import os
from dotenv import load_dotenv

load_dotenv() # take environment variables from .env.

class Globals:
    @classmethod
    def get_env(cls, variable_name):
        value = os.environ[variable_name]
        if value is None: raise KeyError
        else: return value