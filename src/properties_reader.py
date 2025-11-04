from jproperties import Properties

class PropertiesReader:
    def __init__(self, properties_file_path):
        """ Inicializa el lector de propiedades. Args: properties_file_path (str): Ruta al archivo de propiedades """
        self.properties = Properties()
        
        with open(properties_file_path, 'rb') as config_file:
            self.properties.load(config_file)
    
    def get_property(self, key, default=None):
        """ Obtiene una propiedad del archivo. Args: key (str): La clave de la propiedad default: Valor por defecto si la clave no existe Returns: str: El valor de la propiedad """
        return self.properties.get(key, default).data
    
    def get_list_property(self, key, delimiter=',', default=None):
        """ Obtiene una propiedad y la divide en una lista. Args: key (str): La clave de la propiedad delimiter (str): El delimitador para separar la cadena default: Valor por defecto si la clave no existe Returns: list: La lista de valores """
        value = self.get_property(key, default)
        if value:
            return [item.strip() for item in value.split(delimiter)]
        return []
