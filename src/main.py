import os
import sys

from src.config.properties import PropertiesReader
from src.config.steps import definir_pasos
from src.steps.step1 import seleccionar_archivo
from tqdm import tqdm

from src.steps.step2 import leer_archivo
from src.steps.step3 import filtrar_codigo_transaccion_y_respuesta
from src.steps.step4 import guardar_archivo_filtrado
from src.utils.app_state import AppState


def main():
    app_state = AppState()
    app_state.reset()
    configurar(app_state)
    procesar(app_state)


def procesar(appState):
    pasos = definir_pasos()

    # Crear una barra de progreso con los pasos
    with tqdm(total=len(pasos), desc="Conciliacion abonos temporales", colour="green") as pbar:
        # Paso 1: abrir ventana modal para la seleccion del archivo original
        pbar.set_description(f"Paso 1/{len(pasos)}: {pasos[0]}")
        path_archivo = seleccionar_archivo()
        pbar.update(1)

        # Paso 2: lectura del archivo
        pbar.set_description(f"Paso 2/{len(pasos)}: {pasos[1]}")
        leer_archivo(path_archivo, appState)
        pbar.update(1)

        # Paso 3: filtro del archivo
        pbar.set_description(f"Paso 3/{len(pasos)}: {pasos[2]}")
        filtrar_codigo_transaccion_y_respuesta(appState)
        pbar.update(1)

        # Paso 4: guardar el archivo filtrado
        pbar.set_description(f"Paso 4/{len(pasos)}: {pasos[3]}")
        guardar_archivo_filtrado(appState)
        pbar.update(1)

        # Paso 5: Finalizar
        pbar.set_description(f"Paso 5/{len(pasos)}: {pasos[4]}")
        pbar.update(1)


def configurar(appState):
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        appState.set_project_path(base_path)
        config_path = os.path.join(base_path, 'config', 'config.properties')
        config = PropertiesReader(config_path)
        appState.set_configuration(config)
    except Exception as e:
        print(f"Error al leer el archivo de configuración: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
