import pandas as pd

def filtrar_codigo_transaccion_y_respuesta(app_state):
    config = app_state.get_configuration()
    dataframe = app_state.get_dataframe('dataFrameOriginal').copy()
    # Aplicar filtro si está configurado
    filter_codigo_transaccion = config.get_property('filter.codigo_transaccion')
    # Get all transaction codes as a list
    filter_codigos = config.get_list_property('filter.codigo_transaccion.values')

    filter_respuesta = config.get_property('filter.respuesta')
    filter_registros_aplicados = config.get_property('filter.respuesta.registro_aplicado')

    if filter_codigo_transaccion and filter_codigos:
        try:
            # Convertir la columna a numérico, los no convertibles serán NaN
            dataframe[filter_codigo_transaccion] = pd.to_numeric(
                dataframe[filter_codigo_transaccion], 
                errors='coerce'
            )

            # Eliminar filas con valores no numéricos en esa columna
            dataframe = dataframe.dropna(subset=[filter_codigo_transaccion])

            # Convertir a enteros y luego a string para la comparación
            dataframe[filter_codigo_transaccion] = dataframe[filter_codigo_transaccion].astype(int).astype(str)

            # Filtrar solo filas donde el valor esté en los valores permitidos
            mask = dataframe[filter_codigo_transaccion].isin(map(str, filter_codigos))
            dataframe = dataframe[mask]

        except ValueError as e:
            print(f"Error al convertir valores a enteros: {e}")
            # Si hay error en la conversión, no se aplica el filtro
            print("No se pudo aplicar el filtro por códigos de transacción")

    if filter_respuesta and filter_registros_aplicados:
        dataframe[filter_respuesta] = dataframe[filter_respuesta].astype(str).str.capitalize()
        dataframe = dataframe[dataframe[filter_respuesta] == filter_registros_aplicados.capitalize()]
    
    app_state.set_dataframe('dataFrameFiltrado', dataframe)
