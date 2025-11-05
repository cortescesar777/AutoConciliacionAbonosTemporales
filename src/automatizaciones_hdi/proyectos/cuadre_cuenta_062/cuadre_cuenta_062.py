import os
import re
import sys
import glob
import shutil
import datetime
import requests

import pandas 
import openpyxl
import holidays_co
import numpy as np
from openpyxl.worksheet.datavalidation import DataValidation

from proyectos.cuadre_cuenta_062.admin_insumos import AdminInsumos
from utilidades.admin_bd import AdminBDNacional
from utilidades.operaciones_pandas import excel_a_csv


def obtener_ultimo_dia_habil(fecha):

    # convertimos fecha
    if isinstance(fecha, datetime.datetime):
        fecha = fecha.date()

    # obtenemos dias festivos en colombia
    holidays = holidays_co.get_colombia_holidays_by_year(fecha.year)
    holidays = [holidays[i][0] for i in range(len(holidays))]

    # hallamos ultimo dia habil    
    ultimo_habil = fecha - datetime.timedelta(days=1)
    
    # verificamos que este correcto
    while ultimo_habil.weekday() in [5, 6] \
        or ultimo_habil in holidays:

        ultimo_habil = ultimo_habil - datetime.timedelta(days=1)

    #para que tome un día más del ultimo día hábil, por ejemplo, que tome el sábado.
    # ultimo_habil = ultimo_habil + datetime.timedelta(days=1)
    
    return ultimo_habil


class CuadreCuenta062(object):

    nombres_meses = {
        1 : 'Enero',
        2 : 'Febrero', 
        3 : 'Marzo', 
        4 : 'Abril', 
        5 : 'Mayo',
        6 : 'Junio',
        7 : 'Julio',
        8 : 'Agosto',
        9 : 'Septiembre',
        10 : 'Octubre',
        11 : 'Noviembre',
        12 : 'Diciembre'
    }

    
    def __init__(self, params, config):

        self.params = params 
        self.config = config 

        self.fecha = self.params.get('fecha', datetime.date.today())
        self.ultimo_dia_habil = obtener_ultimo_dia_habil(self.fecha)

        self.insumos = AdminInsumos(self.config)
        self.bd_nal = AdminBDNacional(self.params['usuario_nal'], self.params['clave_nal'])


    def obtener_radicado(self, x):
        
        #print(f"{x['radicado']}")
        
        if pandas.isna(x['radicado']) \
            or len(str(x['radicado'])) < 10:

            return int(re.findall(r'\d+', x['forma'])[0])

        elif not str(x['radicado'])[0].isdigit():

            return int(re.findall(r'\d+', x['radicado'])[0])

        elif not str(x['radicado']).isdigit():

            return int(x['radicado'])

        return int(x['radicado'])


    def obtener_hist_lecturas_tiempo_real(self):

        ruta_pagina = f'http://dspp.bancolombia.corp/dep/Depo/Documentos%20compartidos/'\
            'Log%20Lecturas%20Tiempo%20Real/Historico_Lecturas_Tiempo_Real_'\
            f'{self.ultimo_dia_habil.strftime("%Y%m%d")}.xlsb'

        ruta_archivo = f'{self.params["carpeta_ppal"]}'\
            'historico_lecturas_tiempo_real/'\
            f'{ruta_pagina.split("/")[-1]}'


        if self.params['descargar_historico_tiempo_real']:
            resp = requests.get(ruta_pagina)

            if resp.status_code == 200:
                salida = open(ruta_archivo, 'wb')
                salida.write(resp.content)
                salida.close()

            else: 
                print('Error: Verifique acceso a la pagina del historico de lecturas en tiempo real')
                sys.exit()


        print(f"{ruta_archivo}")

        df = pandas.read_excel(ruta_archivo, engine='pyxlsb')

        #df.to_excel('listado_radicados_cta062_inicio.xlsx', index=False)

        df = df[['Número de cuenta', 'Código de la transacción',  'Valor de la transacción', 
                'Observaciones', 'Forma 0210 de la transaccion 199 para el cliente', 'Respuesta']]

        df.columns = ['numero_cuenta', 'codigo_trxn', 'valor_trxn', 
                    'radicado', 'forma', 'respuesta']

        df = df[(df['codigo_trxn'].isin([288, 1716, 1722]))
            & ((df['respuesta'] == 'Registro aplicado') | (df['respuesta'] == 'registro aplicado'))]
        
        if df.empty:
            print(f"Para la fecha del último día hábil {self.ultimo_dia_habil.strftime('%d/%m/%Y')} no se encontraron registros para procesar.")
            sys.exit()    
        
        # df.to_excel('listado_radicados_cta062.xlsx', index=False)
        
        # obtenemos radicado de los que no tienen
        df['radicado'] = df.apply(self.obtener_radicado, axis=1)

        # sacamos los que son para gestionar
        cond = df['radicado'].astype(str).str.len() != 10

        gestionar_lectura_tiempo_real = df[cond].copy()

        if not gestionar_lectura_tiempo_real.empty:
            gestionar_lectura_tiempo_real.to_excel(self.params['carpeta_ppal'] \
                + '/gestion_manual/lecturas_tiempo_real/'
                f'gestion_manual_lecturas_tiempo_real_{self.fecha.strftime("%Y%m%d")}.xlsx',
                index=None)
            print(f'Hay {gestionar_lectura_tiempo_real.shape[0]}'
                ' gestiones manuales para las lecturas de tiempo real')

        df = df[~cond]

        df = df[['numero_cuenta', 'codigo_trxn', 'valor_trxn', 'radicado']]

        # sacamos duplicados
        if not self.params['mantener_duplicados_tiempo_real']:
            df.drop_duplicates(inplace=True)

        return df


    def mover_archivos_respaldos(self, rutas):

        # movemos archivos
        archivos = glob.glob(rutas['directorio_fuente'] + '/*.xlsx')

        for i in archivos:
            shutil.move(
                os.path.join(rutas['directorio_fuente'], i), 
                rutas['directorio_respaldo'])

        return 


    def formatear_texto(self, texto):

        texto = texto.replace('á', 'a')\
            .replace('é', 'e')\
            .replace('í', 'i')\
            .replace('ó', 'o')\
            .replace('ú', 'u')

        texto = texto.lower()

        texto = re.sub(r'[^a-zA-Z0-9\._]', ' ', texto)
        texto = ' '.join(texto.split())

        return texto


    def obtener_lectura_reversos_rcls(self):

        rutas = {
            'directorio_fuente': self.params['carpeta_reversos_rcls'],
            'directorio_respaldo': self.params['carpeta_ppal'] + 'respaldo_lectura_reversos/'}

        rutas_insumos = glob.glob(rutas['directorio_fuente'] + '*.xlsx') \
            + glob.glob(rutas['directorio_fuente'] + '*.csv')
        
        df = []

        for f in rutas_insumos:

            if '.xlsx' in f:
                df += [pandas.read_excel(f)]
            else:
                df += [pandas.read_csv(f)]

        cols = ['numero_cuenta', 'codigo_trxn', 'fecha_proceso', 'valor_trxn', 'radicado']

        if df:
            df = pandas.concat(df, ignore_index=True)
            df = df[['Número de cuenta', 'Número de transacción', 
                    'Fecha\nAAAAMMDD', 'Valor', 'Observaciones']]
            df.columns = cols
        else:
            df = pandas.DataFrame(columns=cols)

        # elimnamos duplicados
        df.drop_duplicates(inplace=True)

        return df


    def obtener_historico_batch(self):

        df = self.insumos.leer_excel('historico_batch')
        
        df = df[(df['codigo_trxn'].isin([288, 1716, 1722]))
            & (df['fecha_proceso'] == int(self.ultimo_dia_habil.strftime('%Y%m%d')))]
        
        return df


    def obtener_info_sap(self):

        nombre_archivo = f'Nuevo_Reporte SAP CRM_{self.fecha.strftime("%d%m%Y")}{self.params["sufijo_archivo_sap"]}.csv'
        # nombre_archivo = 'Nuevo_Reporte SAP CRM_25102024.csv'
        
        # ruta_excel = None
        # ruta_excel = '//Sbmdehcl0/Voperaci/Bggepros/CODSARDC/INFORMES/'\
        #     f'Archivos Planos SAP y LOTUS/SAP/{self.fecha.year}/'\
        #     f'{self.nombres_meses[self.fecha.month]}/{nombre_archivo.replace(".csv", ".xlsx")}'
        
        ruta_excel = self.params['ruta_sap'] + f'{self.fecha.year}/'\
            f'{self.nombres_meses[self.fecha.month]}/{nombre_archivo.replace(".csv", ".xlsx")}'
        
        # ruta_excel = self.params['ruta_sap'] + f'{nombre_archivo.replace(".csv", ".xlsx")}'

        # ruta_csv = 'C:/Users/CRIDIA/OneDrive - Grupo Bancolombia/Conciliacion Reclamos/cuadre_cuenta_062/archivos_sap/' + nombre_archivo
        ruta_csv = self.params['carpeta_ppal'] + 'archivos_sap/' + nombre_archivo

        if os.path.exists(ruta_csv):
            df = pandas.read_csv(ruta_csv, low_memory=False)
            # df = pandas.read_csv(ruta_csv, encoding='iso-8859-1', low_memory=False)
        else:
            df = excel_a_csv([ruta_excel, ruta_csv])

        df = df[['Número_de_Radicado', 'Número_de_Ident', 'Numero_de_producto',
                'Producto/Canal','Tipología', 'Fecha_de_la_transaccion']]

        df.columns = ['radicado', 'nit', 'numero_cuenta', 
                    'producto_canal', 'tipologia', 'fecha_trxn']

        return df


    def completar_formato_total(self, total):
        
        cond = [
            (total['observaciones'] == 'ABONO DNE'),
            (total['observaciones'] == 'ABONO MULTIFUNCIONAL'),
            (total['observaciones'].str.contains('REVERSO'))]

        conceptos = [199095096, 199095144, 199095062]

        total['cuenta_contable_debito'] = np.select(cond, conceptos, default=None)

        cond = [
            (total['observaciones'].str.contains('ABONO')),
            (total['observaciones'] == 'REVERSO DNE'),
            (total['observaciones'] == 'REVERSO MULTIFUNCIONAL')]

        conceptos = [199095062, 199095096, 199095144]

        total['cuenta_contable_credito'] = np.select(cond, conceptos, default=None)

        total['campo_tercero_cuenta_contable_credito'] = np.where(
            total['cuenta_contable_debito'] == 199095062,
            total['nit'], 0)

        total['campo_tercero_cuenta_contable_debito'] = np.where(
            total['cuenta_contable_debito'].isin([199095144, 199095096]),
            total['nit'], 0)

        total['fecha_creacion_solicitud'] = self.fecha
        total['oficina_cuenta_contable_credito'] = 978 
        total['oficina_cuenta_contable_debito'] = 978

        # formateamos valor y damos valor a fecha proceso
        total['fecha_proceso'] = self.ultimo_dia_habil
        total['valor_trxn'] = np.where(
            total['observaciones'].str.contains('REVERSO'), 
            total['valor_trxn']*-1, total['valor_trxn'])

        return total


    def obtener_saldo_cuenta_062(self):

        # consultamos saldo de la cuenta para comparar

        consulta = f'''
            SELECT SUM(GXSD{self.ultimo_dia_habil.day:02})
            FROM VISIONR.GIDBLD 
            WHERE GXNOAC = 199095062
                AND GXNOBR = 978
                AND GXYEAR = {self.ultimo_dia_habil.year}
                AND GXMONT = {self.ultimo_dia_habil.month}
        '''

        saldo = self.bd_nal.consultar(consulta)
        saldo = saldo.values[0, 0]

        return saldo


    def generar_transacciones_agiles(self, total):

        df = total.copy()

        df['valor_trxn'] = df['valor_trxn'].abs()

        cond = [
            (df['cuenta_contable_debito'] == 199095062) & (df['cuenta_contable_credito'] == 199095096), 
            (df['cuenta_contable_debito'] == 199095062) & (df['cuenta_contable_credito'] == 199095144),
            (df['cuenta_contable_debito'] == 199095096) & (df['cuenta_contable_credito'] == 199095062),
            (df['cuenta_contable_debito'] == 199095144) & (df['cuenta_contable_credito'] == 199095062)]

        conceptos_desc = ['EF0022', 'EF0023', 'EF0024', 'EF0055']
        conceptos_ofic = [
            'CORRECCION DEBITO NO ENTREGO CAJEROS',
            'CORRECCION DEBITO NO ENTREGO MULTIFUNCIONALES',
            'REVERSO CORRECCION DEBITO NO ENTREGO CAJEROS',
            'REVER CORRECCI DEBITO NO ENTREGO MULTIFUNCIONALES']

        df['codigo'] = np.select(cond, conceptos_desc, default=None)
        df['descripcion'] = np.select(cond, conceptos_ofic, default=None)
        df['oficina_debito'] = 978
        df['oficina_credito'] = 978
        
        # dsdfsdfsdfsdfsdf
        df_agiles = df[['codigo', 'descripcion','oficina_debito', 'oficina_credito', 
                'oficina_cuenta_contable_debito', 'oficina_cuenta_contable_credito', 
                'nit', 'campo_tercero_cuenta_contable_debito',
                'campo_tercero_cuenta_contable_credito', 'valor_trxn']].copy()

        df_agiles['dia_proceso'] = self.fecha.day  
        df_agiles['mes_proceso'] = self.fecha.month 
        df_agiles['anio_proceso'] = self.fecha.strftime('%y')
        df_agiles['dia_contabilizacion'] = self.fecha.day 
        df_agiles['mes_contabilizacion'] = self.fecha.month 
        df_agiles['anio_contabilizacion'] = self.fecha.strftime('%y')
        df_agiles['numero_comprobante'] = 770500
        df_agiles['trn'] = 88
        df_agiles['campo_c'] = 0
        df_agiles['campo_c_oficina_credito'] = 0
        df_agiles['detalle1'] = df['observaciones']
        df_agiles['detalle2'] = df['radicado']
        df_agiles['cuenta_debito1'] = df_agiles['valor_trxn']
        df_agiles['cuenta_credito1'] = df_agiles['valor_trxn']
        df_agiles = df_agiles.round({'cuenta_debito1': 2, 'cuenta_credito1': 2})
        df_agiles['tercero'] = np.where(df_agiles['codigo'].isin(['EF0024', 'EF0055']), 
            df_agiles['nit'], 0)
        df_agiles['tercero_oficina_credito'] = np.where(df_agiles['codigo'].isin(['EF0022', 'EF0023']),
            df_agiles['nit'], 0)

        cols_vacias = ['campo_a', 'campo_b', 'campo_a1', 'campo_b1', 'campo_c1']\
            + [f'detalle{i}' for i in range(3, 9)]\
            + [f'cuenta_debito{i}' for i in range(2, 9)]\
            + [f'cuenta_credito{i}' for i in range(2, 9)]\

        df_agiles = df_agiles.reindex(df_agiles.columns.tolist() + cols_vacias, axis=1)

        # generar formato final
        df_agiles = df_agiles[[
            'codigo', 'descripcion', 'oficina_debito', 'dia_proceso', 'mes_proceso', 'anio_proceso',
            'dia_contabilizacion', 'mes_contabilizacion', 'anio_contabilizacion', 'oficina_credito',
            'numero_comprobante', 'trn', 'tercero', 'campo_a', 'campo_b', 'campo_c', 'campo_a1', 
            'campo_b1', 'campo_c1', 'tercero_oficina_credito', 'campo_c_oficina_credito', 'detalle1',
            'detalle2', 'detalle3', 'detalle4', 'detalle5', 'detalle6', 'detalle7', 'detalle8',
            'cuenta_debito1', 'cuenta_debito2', 'cuenta_debito3', 'cuenta_debito4', 'cuenta_debito5',
            'cuenta_debito6', 'cuenta_debito7', 'cuenta_debito8', 'cuenta_credito1', 'cuenta_credito2',
            'cuenta_credito3', 'cuenta_credito4', 'cuenta_credito5', 'cuenta_credito6', 'cuenta_credito7', 
            'cuenta_credito8']]

        # renombrar columnas
        df_agiles.columns = ['CÓDIGO', 'DESCRIPCIÓN', 'OFICINA DÉBITO', 'DIA PROCESO', 'MES PROCESO', 
            'AÑO PROCESO', 'DIA CONTABILIZACIÓN', 'MES CONTABILIZACIÓN', 'AÑO CONTABILIZACIÓN', 
            'OFICINA CRÉDITO', 'NUM COMPROBANTE', 'TRN', 'TERCERO', 'CAMPO A', 'CAMPO B', 'CAMPO C', 
            'CAMPO A1', 'CAMPO B1', 'CAMPO C1', 'TERCERO OFICINA CRÉDITO', 'CAMPO C OFICINA CRÉDITO', 
            'DETALLE1', 'DETALLE2', 'DETALLE3', 'DETALLE4', 'DETALLE5', 'DETALLE6', 'DETALLE7', 'DETALLE8', 
            'CUENTA DÉBITO 1', 'CUENTA DÉBITO 2', 'CUENTA DÉBITO 3', 'CUENTA DÉBITO 4', 'CUENTA DÉBITO 5', 
            'CUENTA DÉBITO 6', 'CUENTA DÉBITO 7', 'CUENTA DÉBITO 8', 'CUENTA CRÉDITO 1', 'CUENTA CRÉDITO 2', 
            'CUENTA CRÉDITO 3', 'CUENTA CRÉDITO 4', 'CUENTA CRÉDITO 5', 'CUENTA CRÉDITO 6', 'CUENTA CRÉDITO 7', 
            'CUENTA CRÉDITO 8']

        return df_agiles

    
    def inicializar_cuadre(self):

        rcls_lectura_reversos = self.obtener_lectura_reversos_rcls()
        rcls_tiempo_real = self.obtener_hist_lecturas_tiempo_real()
        historico_batch = self.obtener_historico_batch()

        # cruzamos rcls lectura reversos y historico batch
        cols = ['numero_cuenta', 'fecha_proceso', 'codigo_trxn', 'valor_trxn']
        
        if rcls_lectura_reversos.empty:
            rcls_lectura_depositos = pandas.DataFrame(columns=cols + ['radicado'])
        else:
            rcls_lectura_depositos = rcls_lectura_reversos.merge(historico_batch, 
                on=cols, how='inner')

        # obtenemos informacion de sap
        info_sap = self.obtener_info_sap()

        # juntamos todo
        total = pandas.concat([rcls_tiempo_real, rcls_lectura_depositos], ignore_index=True)
        
        total = total.merge(info_sap, on='radicado', how='inner') 
        
        total = total[['numero_cuenta_x', 'codigo_trxn', 'valor_trxn', 'radicado', 
                        'fecha_proceso', 'nit', 'producto_canal', 'tipologia']]
        total.rename(columns={'numero_cuenta_x': 'numero_cuenta'}, inplace=True)
        total['tipologia'] = total['tipologia'].apply(self.formatear_texto)

        # hallamos observaciones
        cond = [
            (total['tipologia'].str.contains('multifuncional')) & (total['codigo_trxn'].isin([1716, 288])),
            (total['tipologia'].str.contains('multifuncional')) & (total['codigo_trxn'] == 1722),
            (total['tipologia'].str.contains('retiro debito no entrego')) & (total['codigo_trxn'].isin([1716, 288])),
            (total['tipologia'].str.contains('retiro debito no entrego')) & (total['codigo_trxn'] == 1722)]

        conceptos = ['ABONO MULTIFUNCIONAL', 'REVERSO MULTIFUNCIONAL', 'ABONO DNE', 'REVERSO DNE']

        total['observaciones'] = np.select(cond, conceptos, default=None)

        # sacamos los que son para gestion manual
        gestion_manual = total[total['observaciones'].isnull()].copy()
        valor_total_gestion_manual = 0

        #guardamos gestion manual
        if not gestion_manual.empty:
            
            # hallamos suma para comparar en cuadre
            aux = gestion_manual.copy()
            aux.loc[aux['codigo_trxn'] == 1722, 'valor_trxn'] *= -1
            valor_total_gestion_manual = aux['valor_trxn'].sum()

            # guardamos y damos formato para edicion controlada
            gestion_manual.to_excel(self.params['carpeta_ppal'] \
                + f'gestion_manual/gestion_manual_{self.fecha.strftime("%Y%m%d")}.xlsx',
                index=None)

            libro_excel = openpyxl.load_workbook(
                filename=self.params['carpeta_ppal'] \
                + f'gestion_manual/gestion_manual_{self.fecha.strftime("%Y%m%d")}.xlsx')

            # obtenemos hoja con datos
            hoja_gm = libro_excel.active

            # generamos data validation de observaciones
            dv_observaciones = DataValidation(
                type="list", 
                formula1='"ABONO MULTIFUNCIONAL,REVERSO MULTIFUNCIONAL,ABONO DNE,REVERSO DNE"', 
                allow_blank=True)

            # agregamos el data validation a nuestra hoja
            hoja_gm.add_data_validation(dv_observaciones)

            # agregamos dv a columna correspondiente
            dv_observaciones.add(f'I2:I{hoja_gm.max_row}')

            # guardamos nuevamente
            libro_excel.save(self.params['carpeta_ppal'] \
                + f'gestion_manual/gestion_manual_{self.fecha.strftime("%Y%m%d")}.xlsx')

            print(f'Hay {gestion_manual.shape[0]} registros para gestionar manualmente')

        total = total[total['observaciones'].notnull()]

        return total, valor_total_gestion_manual


    def correr_cuadre(self):
        print("Ejecutando correr_cuadre...")
        
        if self.params['gestion_manual']:
            # obtenemos gestion manual
            total = pandas.read_excel(self.params['carpeta_ppal'] \
                + f'gestion_manual/gestion_manual_{self.fecha.strftime("%Y%m%d")}.xlsx')

            valor_total_gestion_manual = 0
        else: 
            # obtenemos inicializacion cuadre
            total, valor_total_gestion_manual = self.inicializar_cuadre()

        # complementamos formato
        total = self.completar_formato_total(total)

        # leemos si es gestion manual para completar toda la info
        if self.params['gestion_manual']:
            aux = pandas.read_excel(self.params['carpeta_ppal'] + f'historico_062_{self.fecha.strftime("%Y%m%d")}.xlsx')
            total = aux.append(total, ignore_index=True)

        # obtenemos saldo
        saldo_bd = self.obtener_saldo_cuenta_062()

        # saldo ejecucion
        saldo_ejec = total['valor_trxn'].sum()

        # obtenemos transacciones agiles
        trans_agiles = self.generar_transacciones_agiles(total)

        print(f'Saldo BD : {saldo_bd}')
        print(f'Saldo Automatizacion : {saldo_ejec}')
        print(f'Saldo Gestion Manual : {valor_total_gestion_manual}')
        print(f'Saldo BD - (Saldo Automatizacion + Saldo Gestion Manual) : {saldo_bd - (saldo_ejec + valor_total_gestion_manual)}')

        # guardamos total
        total.to_excel(self.params['carpeta_ppal'] + f'historico_062_{self.fecha.strftime("%Y%m%d")}.xlsx', index=None)

        # # guardamos respaldo de total
        # total.to_excel(self.params['carpeta_respaldo_historico'] + \
        #     f'Datos conciliación efectivo {self.fecha.day} {self.nombres_meses[self.fecha.month].lower()} {self.fecha.year}.xlsx',
        #     index=None)

        # guardamos transacciones agiles
        trans_agiles.to_excel(self.params['carpeta_ppal'] \
            + f'transacciones_agiles/transacciones_agiles_{self.fecha.strftime("%Y%m%d")}.xlsx', index=None)


        if saldo_bd - (saldo_ejec + valor_total_gestion_manual) == 0:
            
            # movemos archivos de lectura reversos
            rutas = {
                'directorio_fuente': self.params['carpeta_reversos_rcls'],
                'directorio_respaldo': self.params['carpeta_ppal'] + 'respaldo_lectura_reversos/'}

            # mover a respaldo
            self.mover_archivos_respaldos(rutas)

        # cosas que faltan, que hago si los saldos son diferentes? 
        # combobox archivo de salida, gestion adicional

        


