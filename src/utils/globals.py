import os

class Globals:
    @classmethod
    def get_env(cls, variable_name, default=None):
        try:
            value = os.environ[variable_name]
        except KeyError as e:
            if default:
                value = default
            else:
                raise KeyError(e)
        return value