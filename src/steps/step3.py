import pandas as pd

def filtrar_codigo_transaccion_y_respuesta(app_state):
    config = app_state.get_configuration()
    dataframe = app_state.get_dataframe('dataFrameOriginal').copy()
    # Aplicar filtro si está configurado
    filter_codigo_transaccion = config.get_property('filter.codigo_transaccion')
    filter_abonos = config.get_property('filter.codigo_transaccion.abonos')
    filter_reversos = config.get_property('filter.codigo_transaccion.reversos')
    filter_otro = config.get_property('filter.codigo_transaccion.otro')

    filter_respuesta = config.get_property('filter.respuesta')
    filter_registros_aplicados = config.get_property('filter.respuesta.registro_aplicado')

    if filter_codigo_transaccion and filter_abonos and filter_reversos and filter_otro:
        try:
            filter_values = [filter_abonos, filter_reversos, filter_otro]
            
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
            mask = dataframe[filter_codigo_transaccion].isin(map(str, filter_values))
            dataframe = dataframe[mask]

        except ValueError as e:
            print(f"Error al convertir valores a enteros: {e}")
            # Si hay error en la conversión, no se aplica el filtro
            print("No se pudo aplicar el filtro por códigos de transacción")

    if filter_respuesta and filter_registros_aplicados:
        dataframe = dataframe[dataframe[filter_respuesta] == filter_registros_aplicados]
    print(dataframe)
    app_state.set_dataframe('dataFrameFiltrado', dataframe)
