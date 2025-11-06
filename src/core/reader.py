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


def seleccionar_archivo(titulo="Seleccionar archivo", tipos_archivo=None):
    """
    Muestra un diálogo para seleccionar un archivo.

    Args:
        titulo (str): Título del diálogo.
        tipos_archivo (list): Lista de tuplas con descripción y extensión.
                             Ejemplo: [('Archivos Excel', '*.xlsx'), ('Todos los archivos', '*.*')]

    Returns:
        str: Ruta del archivo seleccionado o None si se cancela.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        # Ocultar la ventana principal de Tkinter
        root = tk.Tk()
        root.withdraw()

        # Configurar tipos de archivo por defecto si no se especifican
        if tipos_archivo is None:
            tipos_archivo = [
                ('Archivos Excel', '*.xlsx *.xls')
            ]

        # Mostrar el diálogo de selección de archivo
        ruta_archivo = filedialog.askopenfilename(
            title=titulo,
            filetypes=tipos_archivo
        )

        return ruta_archivo if ruta_archivo else None

    except ImportError:
        print("Error: No se pudo importar tkinter. Asegúrate de tenerlo instalado.")
        return None
    except Exception as e:
        print(f"Error al seleccionar archivo: {str(e)}")
        return None
