import pandas as pd
import os

class ExcelReader:
@staticmethod
    def read_excel_file(file_path, sheet_name=0):
        """ Lee un archivo Excel y lo convierte en un DataFrame. Args: file_path (str): Ruta al archivo Excel sheet_name: Nombre o índice de la hoja a leer (por defecto 0) Returns: DataFrame: Los datos del archivo Excel Raises: FileNotFoundError: Si el archivo no existe ValueError: Si hay un problema al leer el archivo """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo {file_path} no existe")
        
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            raise ValueError(f"Error al leer el archivo Excel {file_path}: {str(e)}")
