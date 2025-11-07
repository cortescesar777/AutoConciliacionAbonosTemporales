import pandas as pd
import os
from datetime import datetime

def guardar_archivo_filtrado(app_state):
    dataframe = app_state.get_dataframe('dataFrameFiltrado').copy()
    
    # Obtener la ruta del proyecto
    project_path = app_state.get_project_path()
    
    # Crear carpeta de salida si no existe
    output_dir = os.path.join(project_path, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generar nombre del archivo con timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'datos_filtrados_{timestamp}.xlsx')
    
    try:
        # Guardar el DataFrame en Excel
        dataframe.to_excel(output_file, index=False, sheet_name='Datos Filtrados')
        return output_file
    except Exception as e:
        print(f"✗ Error al guardar el archivo: {e}")
        return None
