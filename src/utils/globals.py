import os

class Globals:
    @classmethod
    def get_env(cls, variable_name):
        value = os.getenv(variable_name)
        if value is None: raise KeyError
        else: return value