"""
Módulo Singleton para almacenar el estado global de la aplicación.

Proporciona acceso centralizado a variables que se definen durante la ejecución
del programa, como el path del proyecto y los dataframes.

Uso:
    from src.utils.app_state import AppState
    
    state = AppState()
    state.set_project_path('/ruta/del/proyecto')
    state.set_dataframe('df1', dataframe)
    
    path = state.get_project_path()
    df = state.get_dataframe('df1')
"""


class AppState:
    """
    Singleton para almacenar el estado global de la aplicación.
    """
    
    _instance = None
    
    def __new__(cls):
        """Garantiza que solo exista una instancia de AppState."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa el estado de la aplicación."""
        if not self._initialized:
            self._project_path = None
            self._dataframes = {}
            self._configurations = None
            self._initialized = True
    
    def set_project_path(self, path):
        self._project_path = path
    
    def get_project_path(self):
        return self._project_path
    
    def set_dataframe(self, name, dataframe):
        self._dataframes[name] = dataframe
    
    def get_dataframe(self, name, default=None):
        return self._dataframes.get(name, default)
    
    def get_all_dataframes(self):
        return self._dataframes.copy()
    
    def remove_dataframe(self, name):
        if name in self._dataframes:
            del self._dataframes[name]
            return True
        return False

    def set_configuration(self,configuration):
        self._configurations = configuration

    def get_configuration(self):
        return self._configurations
    
    def clear_dataframes(self):
        self._dataframes.clear()
    
    def reset(self):
        self._project_path = None
        self._dataframes.clear()
        self._configurations = None
