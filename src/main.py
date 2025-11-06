import os
import sys
import time

from src.config.properties import PropertiesReader
from src.config.steps import definir_pasos
from src.core.reader import ExcelReader, seleccionar_archivo
from tqdm import tqdm


def main():
    configurar()

    pasos = definir_pasos()
    config = configurar()
    # Crear una barra de progreso con los pasos
    with tqdm(total=len(pasos), desc="Conciliacion abonos temporales") as pbar:
        # Paso 1: abrir ventana modal para la seleccion del archivo original
        pbar.set_description(f"Paso 1/{len(pasos)}: {pasos[1]}")
        path_archivo = seleccionar_archivo()
        pbar.update(1)
        time.sleep(0.5)

        # Paso 2: lectura del archivo
        pbar.set_description(f"Paso 2/{len(pasos)}: {pasos[2]}")
        df1 = ExcelReader.read_excel_file(path_archivo)
        pbar.update(1)
        time.sleep(0.5)

        # Paso 3: filtro del archivo
        pbar.set_description(f"Paso 3/{len(pasos)}: {pasos[3]}")
        filter1(config, df1)
        pbar.update(1)
        time.sleep(0.5)

        # Paso 4: Finalizar
        pbar.set_description(f"Paso 4/{len(pasos)}: {pasos[4]}")
        pbar.update(1)
        time.sleep(0.5)


def configurar():
    """
    Configura la aplicación cargando la configuración desde el archivo de propiedades.
    Retorna el objeto de configuración.
    """
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_path, 'config', 'config.properties')
        config = PropertiesReader(config_path)
        return config
    except Exception as e:
        print(f"Error al leer el archivo de configuración: {str(e)}")
        sys.exit(1)


def cargar_datos(config):
    """
    Carga los datos necesarios para el procesamiento.
    Retorna los datos cargados.
    """
    try:
        # Mostrar diálogo para seleccionar archivo
        ruta_archivo = seleccionar_archivo(
            titulo="Seleccione el archivo de datos",
            tipos_archivo=[
                ('Archivos Excel', '*.xlsx *.xls'),
                ('Archivos CSV', '*.csv')
            ]
        )
        
        if not ruta_archivo:
            print("No se seleccionó ningún archivo. Saliendo...")
            sys.exit(0)
            
        print(f"Cargando datos desde: {ruta_archivo}")
        
        # Determinar el tipo de archivo y cargarlo apropiadamente
        if ruta_archivo.lower().endswith(('.xlsx', '.xls')):
            import pandas as pd
            datos = pd.read_excel(ruta_archivo)
        elif ruta_archivo.lower().endswith('.csv'):
            import pandas as pd
            datos = pd.read_csv(ruta_archivo)
        else:
            print("Formato de archivo no soportado.")
            sys.exit(1)
            
        return datos
        
    except Exception as e:
        print(f"Error al cargar los datos: {str(e)}")
        sys.exit(1)


def procesar_informacion(datos):
    """
    Procesa la información cargada según los requisitos del negocio.
    Retorna los resultados del procesamiento.
    """
    try:
        # Aquí iría la lógica de procesamiento
        print("Procesando información...")
        resultados = {}
        return resultados
    except Exception as e:
        print(f"Error al procesar la información: {str(e)}")
        sys.exit(1)


def generar_reportes(resultados, config):
    """
    Genera los reportes con los resultados del procesamiento.
    """
    try:
        # Aquí iría la lógica para generar reportes
        print("Generando reportes...")
        # Ejemplo: resultados.to_excel('reporte_final.xlsx')
    except Exception as e:
        print(f"Error al generar reportes: {str(e)}")
        sys.exit(1)


def limpiar_recursos():
    """
    Limpia los recursos utilizados durante la ejecución.
    """
    try:
        # Aquí iría la lógica para liberar recursos
        print("Limpiando recursos...")
    except Exception as e:
        print(f"Error al limpiar recursos: {str(e)}")
        sys.exit(1)


def filter1(config, df1):
    # Aplicar filtro si está configurado
    filter_partidas = config.get_property('filter.codigo_transaccion')
    filter_abonos = config.get_property('filter.codigo_transaccion.abonos')
    filter_reversos = config.get_property('filter.codigo_transaccion.reversos')
    filter_otro = config.get_property('filter.codigo_transaccion.otro')

    filter_respuesta = config.get_property('filter.respuesta')
    filter_registros_aplicados = config.get_property('filter.respuesta.registro_aplicado')

    if filter_partidas and filter_abonos and filter_reversos and filter_otro:
        print(f"\nAplicando filtro: {filter_partidas} in ({filter_abonos},{filter_reversos},{filter_otro})")
        df1 = df1[df1[filter_partidas] == filter_abonos] or df1[df1[filter_partidas] == filter_reversos] or df1[df1[filter_partidas] == filter_otro]
        print(f"Archivo 1 después del filtro: {len(df1)} registros")

    if filter_respuesta and filter_registros_aplicados:
        print(f"\nAplicando filtro: {filter_respuesta} in ({filter_registros_aplicados})")
        df1 = df1[df1[filter_respuesta] == filter_registros_aplicados]
        print(f"Archivo 1 después del filtro: {len(df1)} registros")


if __name__ == "__main__":
    main()
