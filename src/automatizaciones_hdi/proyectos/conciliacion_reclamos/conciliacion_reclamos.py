import os
import sys   
import glob
import shutil
import datetime
import itertools

import pandas
import openpyxl
import numpy as np

from utilidades.admin_bd import AdminBDNacional
from utilidades.operaciones_pandas import reducir
from proyectos.conciliacion_reclamos.admin_insumos import AdminInsumos
from proyectos.arqueos_cajeros_sucursales_anterior.admin_tiempo import obtener_ultimo_dia_habil


class ConciliacionReclamos(object):

    NUMERO_CUENTA_DNE = 199095096
    NUMERO_CUENTA_MF = 199095144


    def __init__(self, params, config_dev):
        self.params = params 
        self.config_dev = config_dev 

        self.insumos = AdminInsumos(self.config_dev)

        self.bd_nal = AdminBDNacional(
            self.params['usuario_nal'],
            self.params['clave_nal'])

        self.fecha = self.params.get(
            'fecha',
            datetime.date.today())

    
    def obtener_historico_062(self):
        
        # obtenemos archivo
        fecha_insumo = obtener_ultimo_dia_habil(self.fecha)

        # obtenemos archivo historico de la cuenta 062
        ruta_hist_062 = self.params['carpeta_ppal'] \
            + 'cuadre_cuenta_062/historico_062_' \
            f'{fecha_insumo.strftime("%Y%m%d")}.xlsx'

        hist_062 = pandas.read_excel(ruta_hist_062)

        # ponemos cuenta contable
        hist_062['cuenta_contable'] = np.where(
            hist_062['observaciones'].str.contains('MULTIFUNCIONAL'), 
            self.NUMERO_CUENTA_MF, self.NUMERO_CUENTA_DNE)

        # ponemos naturaleza
        hist_062['naturaleza'] = np.where(
            hist_062['observaciones'].str.contains('REVERSO'), 
            'CR', 'DB')

        # ponemos estado partida y fecha fin
        hist_062['estado_partida'] = 'PENDIENTE'
        hist_062['fecha_fin'] = (self.fecha + datetime.timedelta(days=90)).strftime('%d%m%Y')

        # renombramos  y sacamos columnas necesarias
        hist_062.rename(columns={
            'numero_cuenta': 'cuenta_cliente', 
            'fecha_proceso': 'fecha',
            'oficina_cuenta_contable_debito': 'oficina_cuenta_contable',
            'valor_trxn': 'valor'}, inplace=True)

        hist_062 = hist_062[
            ['cuenta_contable', 'oficina_cuenta_contable', 
            'fecha', 'nit', 'valor', 'radicado', 'observaciones',
            'cuenta_cliente', 'naturaleza', 'estado_partida', 'fecha_fin']]

        # damos formato a las columnas para estandarizar
        hist_062['cuenta_contable'] = hist_062['cuenta_contable'].astype('int64')
        hist_062['valor'] = hist_062['valor'].astype(float)
        hist_062['fecha_fin'] = pandas.to_datetime(hist_062['fecha_fin'], format='%d%m%Y')

        # columna adicional para cruce con partidas
        hist_062['estado_cruce'] = 'SIN CRUZAR'

        return hist_062


    def obtener_saldos(self, cuenta, oficina, fecha):
        
        consulta = f"""
            SELECT SUM(GXSD{fecha.day:02}) AS SALDO
            FROM VISIONR.GIDBLD
            WHERE GXNOAC = '{cuenta}'
                AND GXNOBR = '{oficina}'
                AND CONCAT(GXYEAR, GXMONT) = {fecha.year}{fecha.month}
        """

        r = self.bd_nal.consultar(consulta)

        return r.iloc[0, 0]


    def obtener_datos_golf(self, num_cuenta, oficina_cuenta_contable):

        fecha_insumo = obtener_ultimo_dia_habil(self.fecha)
        
        
        consulta = """
            SELECT  RECFCO, RECTRA, RECTER, RECNCT, RECCVR, RECEST, RECOFC, RECOFO, RECOPE, RECEXP
            FROM SCILIBRAMD.SCIFFMVTOH
            WHERE  RECFCO = {}
                AND (RECEST = 'CAA' OR RECEST = 'CG') 
                AND RECNCT = '{}' 
                AND RECOFC = '{}'
        """

        df = self.bd_nal.consultar(consulta.format(
            fecha_insumo.strftime('%Y%m%d'),
            num_cuenta, oficina_cuenta_contable))

        while fecha_insumo != (self.fecha - datetime.timedelta(days=1)):
             fecha_insumo = fecha_insumo + datetime.timedelta(days=1)
             df_aux = self.bd_nal.consultar(consulta.format(
                 fecha_insumo.strftime('%Y%m%d'),
                 num_cuenta, oficina_cuenta_contable))
             df = df.append(df_aux)

        #df.to_excel('./resultado_consulta.xlsx', index=False)

        # organizamos formato
        #df.to_excel('SCILIBRAMD_SCIFFMVTOH.xlsx', index=False)
        
        df['radicado'] = df['RECEXP'].str.extract(r'(\d+)')
        df['radicado'] = df['radicado'].fillna('0')
        #df['radicado'] = np.where(pandas.isna(df['radicado']), 0, df['radicado'])
        df['radicado'] = df['radicado'].astype(np.int64)
        df['naturaleza'] = np.where(df['RECOPE'] == 1, 'DB', np.where(df['RECOPE'] == 2, 'CR', pandas.NA))
        df['observaciones'] = 'ABONO DNE' if num_cuenta == self.NUMERO_CUENTA_DNE else 'ABONO MULTIFUNCIONAL'
        df['cuenta_cliente'] = 0
        df['fecha_fin'] = self.fecha + datetime.timedelta(days=90)
        df['fecha_fin'] = pandas.to_datetime(df['fecha_fin'])

        df.rename(columns={
            'RECNCT': 'cuenta_contable',
            'RECOFC': 'oficina_cuenta_contable',
            'RECFCO': 'fecha',
            'RECTER': 'nit',
            'RECCVR': 'valor'}, inplace=True)
        df['estado_partida'] = 'PENDIENTE'
        df = df.reindex(columns=df.columns.tolist() + ['fecha_cancelado'])

        df['cuenta_contable'] = df['cuenta_contable'].astype('int64')
        df['oficina_cuenta_contable'] = df['oficina_cuenta_contable'].astype('int64')
        df['fecha'] = pandas.to_datetime(df['fecha'], format='%Y%m%d')
        df['nit'] = df['nit'].astype('int64')
        df['valor'] = df['valor'].astype(float)
        df['valor'] = df['valor'].astype(int)
        df['valor'] = np.where(df['naturaleza'] == 'CR', df['valor']*-1, df['valor'])

        # columna adicional para cruce con partidas
        df['estado_cruce'] = 'SIN CRUZAR'

        df = df[
            ['cuenta_contable', 'oficina_cuenta_contable',
            'fecha', 'nit', 'valor', 'radicado', 'observaciones',
            'cuenta_cliente', 'naturaleza', 'estado_partida', 
            'fecha_fin', 'estado_cruce']]

        return df


    def mover_archivos_respaldos(self, rutas):

        # movemos archivos
        archivos = glob.glob(rutas['directorio_fuente'] + '/*.xlsx')

        for i in archivos:
            shutil.move(
                os.path.join(rutas['directorio_fuente'], i), 
                rutas['directorio_respaldo'])

        return 


    def obtener_datos_otras_redes(self):

        fecha_insumo = obtener_ultimo_dia_habil(self.fecha)
        fecha_insumo = datetime.datetime.combine(fecha_insumo, datetime.datetime.min.time())

        df = self.insumos.leer_excel('otras_redes')
        df = df[df['fecha_abono'] == fecha_insumo].copy()

        df['cuenta_contable'] = self.NUMERO_CUENTA_DNE
        df['oficina_cuenta_contable'] = 978
        df['fecha'] = self.fecha - datetime.timedelta(days=1)
        df['naturaleza'] = np.where(df['observaciones'] == 'REVERSO', 'CR', 'DB')
        df.loc[df['observaciones'] == 'REVERSO', 'valor'] *= -1
        df['observaciones'] = df['observaciones'].str.lower() + ' DNE'
        df['fecha_fin'] = self.fecha + datetime.timedelta(days=90)
        df['estado_partida'] = 'PENDIENTE'
        df['fecha_cancelado'] = ''
        df['valor_partida'] = df['valor'].values
        df['cuenta_cliente'] = 0
        df['cuenta_cliente_recl'] = 0

        # formateamos campos
        df['fecha'] = pandas.to_datetime(df['fecha'])
        df['fecha_creacion'] = pandas.to_datetime(df['fecha_creacion'])
        df['valor'] = df['valor'].astype('float64')
        df['fecha_fin'] = pandas.to_datetime(df['fecha_fin'])
        df['fecha_creacion'] = pandas.to_datetime(df['fecha_creacion'])
        # columna adicional para cruce con partidas
        df['estado_cruce'] = 'CON DETALLE PARTIDA'
        df.drop('fecha_abono', axis=1, inplace=True)

        return df

    def obtener_datos_tarjetas_propias(self):

        fecha_insumo = obtener_ultimo_dia_habil(self.fecha)
        fecha_insumo = datetime.datetime.combine(fecha_insumo, datetime.datetime.min.time())
        
        df = self.insumos.leer_excel('tarjetas_propias')
        df = df[df['fecha_abono'] == fecha_insumo].copy()

        df['cuenta_contable'] = self.NUMERO_CUENTA_DNE
        df['oficina_cuenta_contable'] = 978
        df['fecha'] = self.fecha - datetime.timedelta(days=1)
        df['naturaleza'] = np.where(df['observaciones'] == 'REVERSO', 'CR', 'DB')
        df.loc[df['observaciones'] == 'REVERSO', 'valor'] *= -1
        df['observaciones'] = df['observaciones'].str.lower() + ' DNE'
        #ant se le puso str.lower()
        df['fecha_fin'] = self.fecha + datetime.timedelta(days=90)
        df['estado_partida'] = 'PENDIENTE'
        df['fecha_cancelado'] = ''
        df['valor_partida'] = df['valor'].values
        df['cuenta_cliente'] = 0
        df['cuenta_cliente_recl'] = 0

        # formateamos campos
        df['fecha'] = pandas.to_datetime(df['fecha'])
        df['fecha_creacion'] = pandas.to_datetime(df['fecha_creacion'])
        df['nit'] = df['nit'].astype('int64')
        df['valor'] = df['valor'].astype('float64')
        df['fecha_fin'] = pandas.to_datetime(df['fecha_fin'])
        #nueva línea
        df['fecha_creacion'] = pandas.to_datetime(df['fecha_creacion'])

        # columna adicional para cruce con partidas
        df['estado_cruce'] = 'CON DETALLE PARTIDA'
        #nueva línea
        df.drop('fecha_abono', axis=1, inplace=True)

        return df

    def obtener_datos_nequi(self):

        fecha_insumo = obtener_ultimo_dia_habil(self.fecha)
        fecha_insumo = datetime.datetime.combine(fecha_insumo, datetime.datetime.min.time())
        
        df = self.insumos.leer_excel('requerimientos_nequi')
        df = df[df['fecha_abono'] == fecha_insumo].copy()

        df['cuenta_contable'] = self.NUMERO_CUENTA_DNE
        df['oficina_cuenta_contable'] = 976
        df['fecha'] = self.fecha - datetime.timedelta(days=1)
        df['naturaleza'] = np.where(df['observaciones'] == 'Abono', 'DB', 'CR')
        df.loc[df['observaciones'] != 'Abono', 'valor'] *= -1
        df['observaciones'] = df['observaciones'].str.lower() + ' DNE'
        df['fecha_fin'] = self.fecha + datetime.timedelta(days=90)
        df['estado_partida'] = 'PENDIENTE'
        df['cuenta_cliente'] = 0
        df['cuenta_cliente_recl'] = 0

        # formateamos campos
        df['fecha'] = pandas.to_datetime(df['fecha'])
        df['nit'] = df['nit'].astype('int64')
        df['valor'] = df['valor'].astype('float64')
        df['valor_partida'] = df['valor'].astype('float64')

        # df.to_excel('df_req_nequi_antes.xlsx', index=False)        

        ##modificacion 28/08/2023
        df['radicado'] = df['radicado'].astype(str)
        df.loc[pandas.isna(df['radicado']), 'radicado'] = "0"
        df['radicado'] = df['radicado'].map(lambda x: str(x).replace('correo', ''))
        # df['radicado'] = df['radicado'].map(lambda x: str(x).replace('"', ''))  
        # df['radicado'] = df['radicado'].str.slice(0, 8, 1)

        # df.to_excel('df_req_nequi.xlsx', index=False)
        
        df['radicado'] = df['radicado'].astype('int64')

        df['fecha_fin'] = pandas.to_datetime(df['fecha_fin'])
        df['fecha_creacion'] = pandas.to_datetime(df['fecha_creacion'])
        

        # columna adicional para cruce con partidas
        df['estado_cruce'] = 'CON DETALLE PARTIDA'
        df.drop('fecha_abono', axis=1, inplace=True)

        return df

    
    def obtener_datos_cont(self, rutas):
        
        # leemos datos
        cols = ['cuenta_contable', 'oficina_cuenta_contable', 'fecha', 'nit', 'valor', 'radicado', 
              'observaciones', 'cuenta_cliente', 'naturaleza', 'estado_partida', 'fecha_cancelado', 
              'fecha_fin', 'bacodrel', 'baindrev', 'bacodtra', 'estado_trxn', 'segmento', 'fecha_creacion', 
              'causalidad', 'valor_trxn', 'fecha_trxn', 'codigo_cajero', 'codigo_trxn', 'tira_trxn']

        df = pandas.DataFrame(columns=cols)

        for f in glob.glob(rutas['directorio_fuente'] + '/*.xlsx'):

            df_aux = pandas.read_excel(f)
            df_aux.columns = cols

            df = df.append(df_aux, ignore_index=True)

        df['fecha_fin'] = self.fecha + datetime.timedelta(days=90)

        # formateamos campos
        df['cuenta_contable'] = df['cuenta_contable'].astype('int64')
        df['oficina_cuenta_contable'] = df['oficina_cuenta_contable'].astype('int64')
        df['fecha'] = df['fecha'].apply(self.insumos.formatear_fecha)
        df['nit'] = df['nit'].astype('int64')
        df['valor'] = df['valor'].astype('float64')
        df['valor'] = np.where(df['naturaleza'] == 'CR', -df['valor'], df['valor'])

        ##modificacion 28/08/2023
        df['radicado'] = df['radicado'].astype(str)
        df['radicado'] = df['radicado'].map(lambda x: str(x).replace('correo', '')) 
        df.loc[df['radicado']=='', 'radicado'] = "0"
        
        #df.to_excel('df_problema_radicado.xlsx')
        
        df['radicado'] = df['radicado'].astype('int64')

        df['cuenta_cliente'] = df['cuenta_cliente'].astype('int64')
        df['fecha_fin'] = pandas.to_datetime(df['fecha_fin'])

        # columna adicional para cruce con partidas
        df['estado_cruce'] = 'SIN CRUZAR'

        # ajustes
        df['estado_partida'] = 'PENDIENTE'

        # filtramos
        df = df[['cuenta_contable', 'oficina_cuenta_contable', 'fecha', 'nit', 'valor', 'radicado', 
            'observaciones', 'cuenta_cliente', 'naturaleza', 'estado_partida', 'fecha_fin', 'estado_cruce']].copy()

        return df


    def obtener_datos_bd_ajuste(self):

        fecha_insumo = obtener_ultimo_dia_habil(self.fecha)
 
        consulta = """
            SELECT TIPO_AJUSTE, RADICADO, VALOR_AJUSTE,
                    TERCERO, FECHA_AJUSTE, FECHA_TRANSACCION,
                    CAJERO, TIRA_TRANSACCION
            FROM CISLIBPR.AJUSTECB
            WHERE FECHA_AJUSTE IN ('{}', '{}') 
        """

        df = self.bd_nal.consultar(consulta.format(
            str(int(fecha_insumo.day)) + fecha_insumo.strftime('/%m/%Y'), fecha_insumo.strftime('%d/%m/%Y')))

        while fecha_insumo != (self.fecha - datetime.timedelta(days=1)):
            fecha_insumo = fecha_insumo + datetime.timedelta(days=1)
            df_aux = self.bd_nal.consultar(consulta.format(
                str(int(fecha_insumo.day)) + fecha_insumo.strftime('/%m/%Y'), fecha_insumo.strftime('%d/%m/%Y') ))
            df = df.append(df_aux)

        # renombramos columnas
        df.rename(columns={
            'TIPO_AJUSTE': 'observaciones',
            'RADICADO': 'radicado',
            'VALOR_AJUSTE': 'valor',
            'TERCERO': 'nit',
            'FECHA_AJUSTE': 'fecha',    
            'FECHA_TRANSACCION': 'fecha_trxn',
            'CAJERO': 'codigo_cajero',
            'TIRA_TRANSACCION': 'tira_trxn'
        }, inplace=True)

        # ajustamos valores
        df['nit'] = df['nit'].astype('int64')
        df['fecha'] = pandas.to_datetime(df['fecha'], format='%d/%m/%Y')
        df.loc[df['fecha_trxn'] == '28/12/021', 'fecha_trxn'] = '28/12/2021'
        df['fecha_trxn'] = df['fecha_trxn'].apply(lambda x: self.insumos.formatear_fecha(x))
        df['naturaleza'] = np.where(df['observaciones'] == 'ABONO', 'DB', 'CR')

        df['estado_partida'] = 'PENDIENTE'
        df['fecha_fin'] = self.fecha + datetime.timedelta(days=90)
        df['fecha_fin'] = pandas.to_datetime(df['fecha_fin'])
        df['cuenta_contable'] = self.NUMERO_CUENTA_MF
        df['oficina_cuenta_contable'] = 917
        df['valor'] = df['valor'].astype('float64')
        df['valor'] = np.where(df['naturaleza'] == 'CR', -df['valor'], df['valor'])
        df['valor_partida'] = df['valor'].values
        df['valor_trxn'] = df['valor']
        
        ##modificacion 28/08/2023
        df['radicado'] = df['radicado'].astype(str)
        df['radicado'] = df['radicado'].map(lambda x: str(x).replace('correo', '')) 
        df.loc[df['radicado']=='', 'radicado'] = "0"
        
        df.to_excel('df_radicados.xlsx', index=False)
        
        df['radicado'] = df['radicado'].astype(int)
        #df['radicado'] = df['radicado']

        
        df['cuenta_cliente'] = 0
        df['cuenta_cliente_recl'] = 0
        df['fecha_creacion'] = self.fecha
        df['observaciones'] = df['observaciones'] + ' MULTIFUNCIONAL'

        # fijo tira trxn y codigo cajero
        df = df[(df['tira_trxn'].notnull()) & (df['codigo_cajero'].notnull())]

        # columna adicional para cruce con partidas
        df['estado_cruce'] = 'CON DETALLE PARTIDA' 

        return df


    def formatear_fecha_partidas(self, fecha):

        if not isinstance(fecha, str):
            return fecha

        if len(fecha.strip()) != 10:
            fecha = '0' + fecha.strip()

        if '.' in fecha:
            return pandas.to_datetime(fecha.strip(), format='%d.%m.%Y')
        elif '/' in fecha:
            return pandas.to_datetime(fecha.strip(), format='%d/%m/%Y')

        raise AssertionError(f'Formato nuevo de fecha en partidas {fecha}')


    def obtener_historico_partidas_pendientes(self):

        df = pandas.read_excel(self.params['carpeta_ppal'] \
            + 'conciliacion/historico_partidas_pendientes.xlsx')

        return df


    def obtener_cruces_partidas_ind(self, valores_abonos, valores_partidas):
        
        parejas_indices = []
        partida_no_disponible = []

        for i in valores_abonos.index:
            
            filtro = valores_partidas[lambda x: x == valores_abonos[i]]
            partida_disponible = [k for k in filtro.index if k not in partida_no_disponible]
            filtro = filtro.filter(items=partida_disponible)

            if not filtro.empty:

                abonos_iguales = valores_abonos[lambda x: x == valores_abonos[i]].shape[0]

                if filtro.shape[0] > abonos_iguales:
                    self.indices_partidas_devolver += filtro.index.tolist()
                else:
                    parejas_indices += [(i, filtro.index[0])]
                    partida_no_disponible += [filtro.index[0]]
    

        return parejas_indices


    def obtener_cruces_partidas_suma(self, valores_abonos, valores_partidas):
        
        # print(f"valores_abonos: {valores_abonos}  -  valores_partidas: {valores_partidas}")
        
        parejas_sumas_ini = []
        parejas_sumas = []

        for i in range(2, valores_partidas.shape[0] + 1):
            parejas_sumas_ini += list(itertools.combinations(valores_partidas.index, i))

        for i in range(len(parejas_sumas_ini)):
            parejas_sumas_ini[i] += (valores_partidas.filter(parejas_sumas_ini[i], axis=0).sum(),)

        for i in valores_abonos.index:

            parejas_sumas += [(i, j[:-1]) for j in parejas_sumas_ini if valores_abonos[i] == j[-1]]

        # print(f"parejas_sumas: {parejas_sumas}")

        return parejas_sumas


    def obtener_cancelacion_abonos_ind(self, valores_db, valores_cr):
        
        parejas_indices = []
        cr_no_disponibles = []

        for i in valores_db.index:
            
            filtro = valores_cr[lambda x: x == -valores_db[i]]
            cr_disponibles = [k for k in filtro.index if k not in cr_no_disponibles]
            filtro = filtro.filter(items=cr_disponibles)

            if not filtro.empty:

                parejas_indices += [(i, filtro.index[0])]
                cr_no_disponibles += [filtro.index[0]]
                self.no_disponibles_canc += [i, filtro.index[0]]

        return parejas_indices


    def obtener_cancelacion_abonos_suma(self, valores_db, valores_cr):

        # filtramos innecesarios
        db_disponibles = [i for i in valores_db.index if i not in self.no_disponibles_canc]
        cr_disponibles = [i for i in valores_cr.index if i not in self.no_disponibles_canc]

        valores_db = valores_db.filter(items=db_disponibles)
        valores_cr = valores_cr.filter(items=cr_disponibles)

        if valores_db.empty or valores_cr.empty:
            return []
        
        parejas_sumas_ini = []
        parejas_sumas = []

        for i in range(2, valores_db.shape[0] + 1):
            parejas_sumas_ini += list(itertools.combinations(valores_cr.index, i))

        for i in range(len(parejas_sumas_ini)):
            parejas_sumas_ini[i] += (valores_cr.filter(parejas_sumas_ini[i], axis=0).sum(),)

        for i in valores_db.index:

            parejas_sumas += [(i, j[:-1]) for j in parejas_sumas_ini if valores_db[i] == -j[-1]]

        return parejas_sumas


    def guardar_partidas_devolver(self, partidas):

        nombre_archivo = self.params['carpeta_ppal'] \
            + f'conciliacion/partidas_devolver/partidas_devolver_{self.fecha.strftime("%Y%m%d")}.xlsx'

        partidas['causa_devolucion'] = \
            'ERROR: TRXN PARA JUSTIFICACION INCORRECTA O ABONO HECHO MULTIPLES VECES'

        if os.path.exists(nombre_archivo):
            df = pandas.read_excel(nombre_archivo)
            df = df.append(partidas, ignore_index=True)
        else: 
            df = partidas.copy()

        df.to_excel(nombre_archivo, index=None)

        return 


    def guardar_partidas_cruzadas(self, partidas, carpeta_checkpoints):

        nombre_archivo = self.params['carpeta_ppal'] \
                + 'conciliacion/historico_partidas_conciliadas.xlsx'

        df = pandas.read_excel(nombre_archivo)

        df = df.append(partidas, ignore_index=True)

        df.to_excel(nombre_archivo, index=None)
        df.to_excel(carpeta_checkpoints
            + f'historico_partidas_conciliadas.xlsx', index=None)

        return 


    def cruce_bap(self, df):
        
        # filtramos para cruzar
        # SOLO PARA DNE POR EL MOMENTO
        aux_df = df[(df['cuenta_cliente'].notnull()) 
            & (df['estado_cruce'] == 'CON DETALLE PARTIDA')
            & (df['cuenta_cliente'] != 0)
            & (df['fecha_trxn'].notnull()) 
            & (df['cuenta_contable'] == self.NUMERO_CUENTA_DNE)].copy()


        # obtenemos datos bap 102
        bap = self.obtener_datos_bap102(aux_df)
        # buscamos informacion

        respuestas = []

        for i in aux_df.index:

            fecha_trxn = aux_df.loc[i, 'fecha_trxn']
            cuenta_cliente = aux_df.loc[i, 'cuenta_cliente']

            aux_bap = bap[(bap['BAFECTRA'] == fecha_trxn)
                        & (bap['BANROCTA'] == cuenta_cliente)].copy()
            
            just = aux_bap[(aux_bap['BANROTER'] == aux_df.loc[i, 'codigo_cajero'])
                        & (aux_bap['BANROREC'] == aux_df.loc[i, 'codigo_trxn'])
                        & (aux_bap['BAVLRTRA'] == aux_df.loc[i, 'valor_trxn'])]
            
            opc = aux_bap[((aux_bap['BANROTER'] != aux_df.loc[i, 'codigo_cajero'])
                        | (aux_bap['BANROREC'] != aux_df.loc[i, 'codigo_trxn']))
                        & (aux_bap['BAVLRTRA'] == aux_df.loc[i, 'valor_trxn'])
                        & (aux_bap['RESULTADO'] == 0)]
            
            if not just.empty and just['RESULTADO'].values[0] == 0:
                
                respuestas += [{
                    'estado': True,
                    'fuente': 'justificado',
                    'bap': just,
                    'id_total_contab': i
                }]
                
            elif (just.empty or just['RESULTADO'].values[0] != 0) \
                and opc.shape[0] == 1:

                respuestas += [{
                    'estado': True,
                    'fuente': 'opcional',
                    'bap': opc,
                    'id_total_contab': i
                }]

            else:
                # que pasa con las que no aparecen
                # que pasa con las que no aparecen y las opcionales hay mas de una
                # que pasa con las que aparecen con codigo malo y opcionales no hay o hay mas de una
                pass 

        cols_partidas = ['radicado', 'nit', 'cuenta_cliente', 'segmento', 'fecha_creacion', 
            'causalidad', 'valor_trxn', 'fecha_trxn', 'codigo_cajero', 'codigo_trxn', 
            'tira_trxn', 'valor']						

        df_partidas_devolver = pandas.DataFrame(columns=cols_partidas)

        for i in respuestas:

            idx = i['id_total_contab']
            datos = i['bap']

            df.loc[idx, ['bacodrel', 'baindrev', 'bacodtra']] \
                = datos[['BACODREL', 'BAINDREV', 'BACODTRA']].iloc[0].tolist()
            df.loc[idx, 'estado_trxn'] = 'EXITOSA'

            if i['fuente'] == 'opcional':

                # guardamos partida mala
                df_partidas_devolver = df_partidas_devolver.append(
                    df.loc[idx, cols_partidas], ignore_index=True)

                df.loc[idx, ['fecha_trxn', 'codigo_cajero', 'codigo_trxn']] \
                    = datos[['BAFECTRA', 'BANROTER', 'BANROREC']].iloc[0].tolist()
                df.loc[idx, 'tira_trxn'] = 'PENDIENTE'

            df.loc[idx, 'estado_cruce'] = 'CON DETALLE PARTIDA - BAP'
            
        return df, df_partidas_devolver


    def obtener_datos_bap102(self, abonos):

        # abonos.to_excel('df_aux_abonos.xlsx')

        bap = []

        cols = ['BAFECTRA', 'BAFECPRO', 'BANROCTA', 'BACODTRA', 'BANROREC', 
                    'BANROTER', 'BANUMTAR', 'BACODREL', 'BAINDREV', 'BAVLRTRA']

        for i in abonos['fecha_trxn'].unique():

            # df_abonos = abonos.loc[abonos['fecha_trxn'] == i]

            fecha = int(pandas.to_datetime(i).strftime('%m%d%y'))
            # df_abonos.to_excel(f'df_abonos_{fecha}.xlsx')
            
            fecha_t_1 = int((pandas.to_datetime(i) - datetime.timedelta(days=1)).strftime('%m%d%y'))
            cuentas_cliente = abonos.loc[abonos['fecha_trxn'] == i, 'cuenta_cliente'].unique().tolist()
            cuentas_cliente = tuple([f'{int(i):018}' for i in cuentas_cliente])

            if len(cuentas_cliente) == 1:
                cuentas_cliente = str(cuentas_cliente).replace(',', '')

            # print(f"fecha: {fecha}")
            # print(f"fecha_t_1: {fecha_t_1}")
            # print(f"cuentas_cliente: {cuentas_cliente}")

            consulta = f"""
                SELECT BAFECTRA, BAFECPRO, BANROCTA, BACODTRA, BANROREC, 
                    BANROTER, BANUMTAR, BACODREL, BAINDREV, BAVLRTRA
                FROM CABLIBRANL.CABFFB102H
                WHERE BAFECPRO BETWEEN {int(fecha_t_1)} AND {int(fecha)}
                    AND BANROCTA IN {cuentas_cliente}
            """

            # print(f"consulta: {consulta}")
            
            datos_consulta = self.bd_nal.consultar(consulta)
            # datos_consulta.to_excel(f'datos_consulta_{fecha}.xlsx', index=False)

            bap += [datos_consulta]

        if not bap:
            bap = pandas.DataFrame(columns=cols + ['RESULTADO'])
            return bap

        bap = pandas.concat(bap, ignore_index=True)
        bap['BAFECTRA'] = bap['BAFECTRA'].astype(int).astype(str)
        bap['BAFECTRA'] = bap['BAFECTRA'].apply(lambda x: x.rjust(6, '0'))
        bap['BAFECTRA'] = pandas.to_datetime(bap['BAFECTRA'], format='%m%d%y')
        bap['BAFECPRO'] = bap['BAFECPRO'].astype(int).astype(str)
        bap['BAFECPRO'] = bap['BAFECPRO'].apply(lambda x: x.rjust(6, '0'))
        bap['BAFECPRO'] = pandas.to_datetime(bap['BAFECPRO'], format='%m%d%y')
        bap['BANROCTA'] = bap['BANROCTA'].astype('int64')
        bap['BANROREC'] = bap['BANROREC'].astype('int64')
        bap['BANROTER'] = bap['BANROTER'].astype('int64')
        bap['BAINDREV'] = bap['BAINDREV'].astype('int64')
        bap['BACODREL'] = bap['BACODREL'].astype('int64')
        bap['RESULTADO'] = bap['BAINDREV'].values + bap['BACODREL'].values

        return bap


    def conciliar(self):

        #dependencias = ['reclamos', 'cajeros_produccion']

        # obtenemos archivo de cuenta_reclamos
        cp = self.insumos.leer_excel('cajeros_produccion') 
        reclamos = self.insumos.leer_excel('reclamos')
        #cp = self.insumos.leer_multiples_excel(dependencias)
        reclamos.to_excel('reclamos.xlsx', index=False)
        
        # obtenemos historico de cuenta 062
        hist_062 = self.obtener_historico_062()
        hist_062.to_excel('hist_062.xlsx', index=False)
        
        # obtenemos emulacion de la cuenta 096 - golf
        emulacion_096 = self.obtener_datos_golf(self.NUMERO_CUENTA_DNE, 978)
        emulacion_096.to_excel('emulacion_096.xlsx', index=False)
        
         # obtenemos emulacion de la cuenta 096 - golf
        emulacion_144_917 = self.obtener_datos_golf(self.NUMERO_CUENTA_MF, 917)
        emulacion_144_917.to_excel('emulacion_144_917.xlsx', index=False)
        
        # obtenemos otras redes
        otras_redes = self.obtener_datos_otras_redes()
        otras_redes.to_excel('otras_redes.xlsx', index=False)
        
        
        #obtener tarjetas propias
        tarjetas_propias = self.obtener_datos_tarjetas_propias()
        tarjetas_propias.to_excel('tarjetas_propias.xlsx', index=False)
        
        # obtenemos nequi
        nequi = self.obtener_datos_nequi()
        nequi.to_excel('nequi.xlsx', index=False)
        
        # obtenemos adicionales - Juan Andres Giraldo encargado
        # cuenta self.NUMERO_CUENTA_DNE
        rutas_cont_096 = {
           'directorio_fuente': self.params['carpeta_ppal'] + 'conciliacion/contabilidad_manual/096/' ,
           'directorio_respaldo': self.params['carpeta_ppal'] + 'conciliacion/respaldos/contabilidad_manual/096/'}
        contabilidad_096 = self.obtener_datos_cont(rutas=rutas_cont_096)
        contabilidad_096.to_excel('contabilidad_096.xlsx', index=False)
        
        # obtenemos emulacion de la cuenta 144 - golf
        emulacion_144_978 = self.obtener_datos_golf(self.NUMERO_CUENTA_MF, 978)
        emulacion_144_978.to_excel('emulacion_144_978.xlsx', index=False)
        
        # obtenemos adicionales - Juan Andres Giraldo encargado
        # cuenta self.NUMERO_CUENTA_MF
        rutas_cont_144_978 = {
           'directorio_fuente': self.params['carpeta_ppal'] + 'conciliacion/contabilidad_manual/144_978/' ,
           'directorio_respaldo': self.params['carpeta_ppal'] + 'conciliacion/respaldos/contabilidad_manual/144_978/'}
        contabilidad_144_978 = self.obtener_datos_cont(rutas=rutas_cont_144_978)
        contabilidad_144_978.to_excel('contabilidad_144_978.xlsx', index=False)
        
        # obtenemos datos cuenta 144 - 917
        emulacion_cb_144_917 = self.obtener_datos_bd_ajuste()
        emulacion_cb_144_917.to_excel('emulacion_cb_144_917.xlsx', index=False)
        # juntamos ambas emulaciones de la 917
        #emulacion_cb_144_917 = emulacion_cb_144_917.append(emulacion_144_917, ignore_index=True)
        #emulacion_cb_144_917.drop_duplicates(subset=['nit', 'valor'], inplace=True)
        
        # obtenemos adicionales - Juan Andres Giraldo encargado
        # cuenta self.NUMERO_CUENTA_MF 917
        rutas_cont_144_917 = {
           'directorio_fuente': self.params['carpeta_ppal'] + 'conciliacion/contabilidad_manual/144_917/' ,
           'directorio_respaldo': self.params['carpeta_ppal'] + 'conciliacion/respaldos/contabilidad_manual/144_917/'}
        contabilidad_144_917 = self.obtener_datos_cont(rutas=rutas_cont_144_917)
        contabilidad_144_917.to_excel('contabilidad_144_917.xlsx', index=False)
        
        # juntar todo
        total_contab = pandas.concat([
            reclamos, hist_062, emulacion_cb_144_917, tarjetas_propias,
            otras_redes, nequi, contabilidad_096, emulacion_144_978, emulacion_096,
            contabilidad_144_978, contabilidad_144_917],
            ignore_index=True) # quite cb
        total_contab.to_excel('total_contab_primero.xlsx', index=False)
        
        
        # sacamos los duplicados y cancelados
        total_contab = total_contab[~total_contab['estado_partida'].isin(['CANCELADO', 'DUPLICADO'])]

        # arreglar naturaleza
        total_contab['naturaleza'] = np.where(total_contab['valor'] < 0, 'CR', total_contab['naturaleza'])
        total_contab.to_excel('total_contab_2.xlsx', index=False)
        
        # obtenemos detalle partidas
        partidas = self.obtener_historico_partidas_pendientes()      
        partidas.to_excel('partidas.xlsx', index=False)
        
        
        print('ANTES DE TODO: ', total_contab['valor'].sum())

        # CRUCE DE ABONOS CON PARTIDAS
        self.indices_partidas_devolver = []
        
        # separamos los abonos para cruzar con partidas
        total_contab.to_excel("total_contab_abonos_para_cruzar.xlsx")
        abonos_para_cruzar = total_contab[(total_contab['naturaleza'] == 'DB') 
            & (total_contab['estado_cruce'] == 'SIN CRUZAR')].copy()
        
        abonos_para_cruzar.to_excel('abonos_para_cruzar.xlsx')

        parejas_cruces_ind = []
        parejas_cruces_sumas = []

        for i in abonos_para_cruzar.set_index(['nit', 'radicado']).index.unique():

            aux_partidas = partidas[partidas.set_index(['nit', 'radicado']).index.isin([i])]
            aux_abonos = abonos_para_cruzar[abonos_para_cruzar.set_index(['nit', 'radicado']).index.isin([i])]
            
            # print(f"aux_partidas: {aux_partidas}")
            # print(f"aux_abonos: {aux_abonos}")

            if aux_partidas.shape[0] == 0:
                continue
            
            # print(f"index: {i}")
            # print(f"aux_partidas: {aux_partidas}")
            # print(f"aux_abonos: {aux_abonos}")
            
            # obtnemos parejas que se crucen individualmente
            parejas_cruces_ind += self.obtener_cruces_partidas_ind(aux_abonos['valor'], aux_partidas['valor'])
            
            # print(f"parejas_cruces_ind: {parejas_cruces_ind}")

            # obtenemos parejas que se crucen por suma
            parejas_cruces_sumas += self.obtener_cruces_partidas_suma(aux_abonos['valor'], aux_partidas['valor'])

        # revisar devueltos que estan en parejas
        aux_partidas_cruce_sumas = [j for k in parejas_cruces_sumas for j in k[-1]]
        self.indices_partidas_devolver = [
            j for j in self.indices_partidas_devolver 
            if j not in aux_partidas_cruce_sumas]

        # revisar repetidos
        parejas_cruces_ind = pandas.DataFrame(parejas_cruces_ind)
        parejas_cruces_ind = parejas_cruces_ind[~parejas_cruces_ind.duplicated(subset=1)]
        parejas_cruces_ind = parejas_cruces_ind.values.tolist()

        # cruzar y cambiar estado de cruzados
        # primero los individuales
        cols_partidas = [
            'segmento', 'fecha_creacion', 'causalidad', 'cuenta_cliente', 
            'valor', 'valor_trxn', 'fecha_trxn', 'codigo_cajero',
            'codigo_trxn', 'tira_trxn']

        cols_abonos = [
            'segmento', 'fecha_creacion', 'causalidad', 'cuenta_cliente_recl',
            'valor_partida', 'valor_trxn', 'fecha_trxn', 'codigo_cajero',
            'codigo_trxn', 'tira_trxn']

        indices_partidas_cruzadas = []
        
        for i in parejas_cruces_ind:

            total_contab.loc[i[0], cols_abonos] = partidas.loc[i[1], cols_partidas].values
            total_contab.loc[i[0], 'estado_cruce'] = 'CON DETALLE PARTIDA' 
            indices_partidas_cruzadas += [i[1]]
            
        total_contab.to_excel('total_contab_cruce_abonos.xlsx', index=False)
        partidas.to_excel('partidas_cruces.xlsx', index=False)
        
        # luego los de combinacion
        for i in parejas_cruces_sumas:
            
            print(f"i: {i}")
            print(f"i[0]: {i[0]}")
            print(f"i[1][0]: {i[1][0]}")
            
            print(f"{partidas.loc[i[1][0], cols_partidas]}")
            
            total_contab.loc[i[0], cols_abonos] = partidas.loc[i[1][0], cols_partidas].values
            
            print(f"{total_contab.loc[i[0], cols_abonos]}")
            
            print(f"{type(total_contab.loc[i[0], 'valor_partida'])}")
            print(f"{total_contab.loc[i[0], cols_abonos]}")

            # dfp = pandas.DataFrame([total_contab.loc[i[0], 'valor_partida']], columns='valor_partida')

            if not pandas.isna(total_contab.loc[i[0], 'valor_partida']):
                # if dfp.shape[0] > 1:
                #     print("Alerta: Filas duplicadas en valor partida")
                # else:
                total_contab.loc[i[0], 'valor'] = total_contab.loc[i[0], 'valor_partida']
                
            total_contab.loc[i[0], 'estado_cruce'] = 'CON DETALLE PARTIDA'
            aux_reg = total_contab.loc[i[0], :].copy()

            indices_partidas_cruzadas += i[1]

            for j in i[1][1:]:
                aux_reg[cols_abonos] = partidas.loc[j, cols_partidas].values
                if not pandas.isna(aux_reg['valor_partida']):
                    aux_reg['valor'] = aux_reg['valor_partida']

                total_contab = total_contab.append(aux_reg)

        # cambiar estado de devueltos y cruzados
        self.indices_partidas_devolver = list(self.indices_partidas_devolver)
        partidas_devolver = partidas[partidas.index.isin(self.indices_partidas_devolver)].copy()
        partidas_cruzadas = partidas[partidas.index.isin(indices_partidas_cruzadas)].copy()
        partidas_pendientes = partidas[~partidas.index.isin(
            self.indices_partidas_devolver + indices_partidas_cruzadas)].copy()

        # reseteamos indices abonos
        total_contab.reset_index(drop=True, inplace=True)
        total_contab.to_excel('total_contab_desp_cruces.xlsx', index=False)
        
        
        print('DESPUES DE CRUCE PARTIDAS: ', total_contab['valor'].sum())

        # CRUCE CON BAP
        total_contab, devueltos_bap = self.cruce_bap(total_contab)
        partidas_devolver = partidas_devolver.append(devueltos_bap, ignore_index=True)
        #total_contab.to_excel('total_contab_desp_cruce_bap.xlsx', index=False)


        print('DESPUES DE CRUCE BAP: ', total_contab['valor'].sum())

        # CRUCE PARA CANCELAR
        abonos_para_cancelar = total_contab.copy()

        parejas_cancelacion_ind = []
        parejas_cancelacion_sumas = []

        for i in abonos_para_cancelar.set_index(['nit', 'radicado']).index.unique():
            
            aux_db = abonos_para_cancelar[
                (abonos_para_cancelar.set_index(['nit', 'radicado']).index.isin([i]))
                & (abonos_para_cancelar['naturaleza'] == 'DB')].copy()

            aux_cr = abonos_para_cancelar[
                (abonos_para_cancelar.set_index(['nit', 'radicado']).index.isin([i]))
                & (abonos_para_cancelar['naturaleza'] == 'CR')].copy()


            if len(aux_db['cuenta_contable'].unique()) > 0:
                aux_cr = aux_cr[
                    aux_cr['cuenta_contable'] == aux_db['cuenta_contable'].unique()[0]].copy()

            # si no hay CR salgo
            if aux_cr.shape[0] == 0:
                continue

            self.no_disponibles_canc = []

            # si hay CR verifico individualidad de valores
            parejas_cancelacion_ind += self.obtener_cancelacion_abonos_ind(aux_db['valor'], aux_cr['valor'])

            # si hay CR verifico parejas de cancelacion
            parejas_cancelacion_sumas += self.obtener_cancelacion_abonos_suma(aux_db['valor'], aux_cr['valor'])

        # revisar repetidos
        parejas_cancelacion_ind = pandas.DataFrame(parejas_cancelacion_ind)
        parejas_cancelacion_ind = parejas_cancelacion_ind[~parejas_cancelacion_ind.duplicated(subset=1)]
        parejas_cancelacion_ind = parejas_cancelacion_ind.values.tolist()

        # sacamos lista con abonos que ya cruzaron
        indices_cruzados = [j for i in parejas_cancelacion_ind for j in i]

        # filtramos parejas de sumas
        parejas_canc_sumas_filtradas = []

        for i in parejas_cancelacion_sumas:

            aux = [i[0]] + list(i[1]) 
            estado = True

            for j in aux:
                if j in indices_cruzados:
                    estado = False 
                    break

            if estado:
                parejas_canc_sumas_filtradas += [i]


        # cancelo parejas
        for i in parejas_cancelacion_ind:

            total_contab.loc[i, ['estado_partida', 'fecha_cancelacion']] = 'CANCELADO', self.fecha

        # luego los de combinacion
        for i in parejas_canc_sumas_filtradas:
            
            total_contab.loc[i[0], ['estado_partida', 'fecha_cancelacion']] = 'CANCELADO', self.fecha
            total_contab.loc[i[1], ['estado_partida', 'fecha_cancelacion']] = 'CANCELADO', self.fecha

        # guardo archivo de cancelados y de abonos pendientes
        cond = total_contab['estado_partida'] == 'CANCELADO'
        abonos_cancelados = total_contab[cond].copy()
        total_contab = total_contab[~cond].copy()
        
        #total_contab.to_excel('total_contab_desp_cruce_cancelacion.xlsx', index=False)

        print('DESPUES DE CRUCE CANCELACION: ', total_contab['valor'].sum())

        # SALIDA DE TEXTO
        # obtener saldos
        saldo_096 = self.obtener_saldos(self.NUMERO_CUENTA_DNE, 978, self.fecha - datetime.timedelta(days=1))
        saldo_096976 = self.obtener_saldos(self.NUMERO_CUENTA_DNE, 976, self.fecha - datetime.timedelta(days=1))
        saldo_144978 = self.obtener_saldos(self.NUMERO_CUENTA_MF, 978, self.fecha - datetime.timedelta(days=1))
        saldo_144917 = self.obtener_saldos(self.NUMERO_CUENTA_MF, 917, self.fecha - datetime.timedelta(days=1))

        total_contab.to_excel('total_contab_saldos_cuentas.xlsx', index=False)
        saldo_datos_144917_ver =  total_contab.loc[(total_contab['oficina_cuenta_contable'] == 978) 
            & (total_contab['cuenta_contable'] == self.NUMERO_CUENTA_MF), :]
        saldo_datos_144917_ver.to_excel('saldos_144978_revisar_valor.xlsx', index=False)
        
        saldo_datos_096 = total_contab.loc[
            (total_contab['oficina_cuenta_contable'] == 978) 
            & (total_contab['cuenta_contable'] == self.NUMERO_CUENTA_DNE), 'valor'].sum()

        saldo_datos_144978 = total_contab.loc[
            (total_contab['oficina_cuenta_contable'] == 978) 
            & (total_contab['cuenta_contable'] == self.NUMERO_CUENTA_MF), 'valor'].sum()

        saldo_datos_144917 = total_contab.loc[
            (total_contab['oficina_cuenta_contable'] == 917) 
            & (total_contab['cuenta_contable'] == self.NUMERO_CUENTA_MF), 'valor'].sum()

        saldo_datos_096976 = total_contab.loc[
            (total_contab['oficina_cuenta_contable'] == 976) 
            & (total_contab['cuenta_contable'] == self.NUMERO_CUENTA_DNE), 'valor'].sum()
        
        print('Ejecucion del dia : ', self.fecha.strftime('%Y%m%d'))
        print()
        print('096')
        print(f"Número cuenta: {self.NUMERO_CUENTA_DNE}")
        print('bd : ', saldo_096)
        print('datos : ', saldo_datos_096)
        print('diferencia : ', saldo_096 - saldo_datos_096)
        print()

        print('144-978')
        print(f"Número cuenta: {self.NUMERO_CUENTA_MF}")
        print('bd : ', saldo_144978)
        print('datos : ', saldo_datos_144978)
        print('diferencia : ', saldo_144978 - saldo_datos_144978)
        print()

        print('144-917')
        print(f"Número cuenta: {self.NUMERO_CUENTA_MF}")
        print('bd : ', saldo_144917)
        print('datos : ', saldo_datos_144917)
        print('diferencia : ', saldo_144917 - saldo_datos_144917)
        print()

        print('096-976')
        print(f"Número cuenta: {self.NUMERO_CUENTA_DNE}")
        print('bd : ', saldo_096976)
        print('datos : ', saldo_datos_096976)
        print('diferencia : ', saldo_096976 - saldo_datos_096976)
        print()

        # guardamos todos nuestros insumos si y solo si esta cuadrado
        if ((saldo_096 - saldo_datos_096 == 0) \
            and (saldo_144978 - saldo_datos_144978 == 0) \
            and (saldo_144917 - saldo_datos_144917 == 0) \
            and (saldo_096976 - saldo_datos_096976) == 0) \
            or not self.params['guardar_solo_si_cuadra']:

            carpeta_checkpoints = self.params['carpeta_ppal'] \
                + f'conciliacion/checkpoints/{self.fecha.strftime("%Y%m%d")}/'

            # creamos carpeta de checkpoint
            if not os.path.exists(carpeta_checkpoints):
                os.makedirs(carpeta_checkpoints)

            # guardamos todo de partidas
            self.guardar_partidas_devolver(partidas_devolver)
            self.guardar_partidas_cruzadas(partidas_cruzadas, carpeta_checkpoints)
            partidas_pendientes.to_excel(self.params['carpeta_ppal']
                + 'conciliacion/historico_partidas_pendientes.xlsx',
                index=None)
            partidas_pendientes.to_excel(carpeta_checkpoints 
                + 'historico_partidas_pendientes.xlsx',
                index=None)

            # guardamos todo de abonos
            abonos_cancelados.to_excel(self.params['carpeta_ppal'] 
                + f'conciliacion/cancelados/cancelados_{self.fecha.strftime("%Y%m%d")}.xlsx',
                index=None)
            total_contab.to_excel(self.params['carpeta_ppal'] 
                + 'conciliacion/historico_reclamos_pendientes.xlsx', 
                index=None)
            total_contab.to_excel(carpeta_checkpoints 
                + 'historico_reclamos_pendientes.xlsx', 
                index=None)

            # guardamos historico cancelados
            hist_cancelados = pandas.read_excel(self.params['carpeta_ppal'] \
                + 'conciliacion/historico_cancelados.xlsx')
            hist_cancelados = hist_cancelados.append(abonos_cancelados, ignore_index=True)
            hist_cancelados.to_excel(self.params['carpeta_ppal'] \
                + 'conciliacion/historico_cancelados.xlsx', index=None)
            hist_cancelados.to_excel(carpeta_checkpoints \
                + 'historico_cancelados.xlsx', index=None)

            # guardamos saldo diario
            dict_saldo = {
                'fecha': self.fecha,
                'saldo_bd_096': saldo_096,
                'saldo_datos_096': saldo_datos_096,
                'saldo_bd_144_978': saldo_144978,
                'saldo_datos_144_978': saldo_datos_144978,
                'saldo_bd_144_917': saldo_144917,
                'saldo_datos_144_917': saldo_datos_144917,
                'saldo_bd_096_976': saldo_096976,
                'saldo_datos_096_976': saldo_datos_096976,
                'dif_096': saldo_096 - saldo_datos_096,
                'dif_096_976': saldo_096976 - saldo_datos_096976,
                'dif_144_978': saldo_144978 - saldo_datos_144978,
                'dif_144_917': saldo_144917 - saldo_datos_144917
            }

            saldo_diario = pandas.read_excel(self.params['carpeta_ppal'] 
                + 'conciliacion/saldo_diario.xlsx')
            saldo_diario = saldo_diario.append(dict_saldo, ignore_index=True)
            saldo_diario.to_excel(self.params['carpeta_ppal'] 
                + 'conciliacion/saldo_diario.xlsx', index=None)
            saldo_diario.to_excel(carpeta_checkpoints
                + 'saldo_diario.xlsx', index=None)

            # guardamos respaldos
            self.mover_archivos_respaldos(rutas_cont_096)
            self.mover_archivos_respaldos(rutas_cont_144_978)
            self.mover_archivos_respaldos(rutas_cont_144_917)


        else:
            print('No ha cuadrado, por lo tanto, no se han guardado los insumos')


    
    def generar_reporte_para_conciliacion(self):

        # dependencias
        dependencias = ['reclamos', 'cajeros_produccion']

        # leer archivo de reclamos pendientes
        reclamos, cp = self.insumos.leer_multiples_excel(dependencias)

        # revisar cuales no tienen fecha de envio
        conciliar = reclamos[ 
            (reclamos['fecha_envio_para_conciliacion'].isnull()) 
            & (reclamos['estado_cruce'].str.contains('CON DETALLE PARTIDA'))
            & (reclamos['tira_trxn'].str.lower() != 'reversado')].copy()

        # poner fecha de envio hoy
        reclamos.loc[conciliar.index, 'fecha_envio_para_conciliacion'] = self.fecha 
        conciliar['fecha_envio_para_conciliacion'] = self.fecha 

        # poner columna de fecha de conciliacion
        conciliar['fecha_conciliacion'] = ''


        # formateamos los registros para conciliar
        conciliar.rename(columns={
            'fecha': 'Fecha Abono',
            'nit': 'Cédula',
            'codigo_cajero': 'Cajero',
            'codigo_trxn': 'Transacción',
            'fecha_trxn': 'Fecha Transacción',
            'tira_trxn': 'Error',
            'valor_trxn': 'Valor De La Transacción',
            'valor': 'Valor abonado al Cliente',
            'cuenta_cliente_recl': 'Número De Cuenta',
            'causalidad': 'OBSERVACIONES',
            'oficina_cuenta_contable': 'Código de Oficina',
            'fecha_creacion': 'FECHA DE RADICACION',
            'segmento': 'Segmento',
            'radicado': 'Nro. Radicado'
        }, inplace=True)

        # formateamos columnas
        conciliar['Cajero'] = conciliar['Cajero'].astype('int64')
        cp['codigo_cajero'] = cp['codigo_cajero'].astype('int64')

        # agregamos columnas adicionales y vacias
        conciliar = conciliar.merge(cp[['codigo_cajero', 'tdv', 'codigo_suc']],
            left_on='Cajero', right_on='codigo_cajero', how='left')

        conciliar.rename(columns={
            'tdv': 'Transportadora',
            'codigo_suc': 'Nro. Sucursal',
        }, inplace=True)

        conciliar.drop('codigo_cajero', axis=1, inplace=True)

        conciliar['Número De Tarjeta'] = ''
        conciliar['Fecha reclamo sistema (AAAAMMDD)'] = ''
        conciliar['Valor transferido a la cuenta temporal de reclamos'] = ''
        conciliar['Fecha de Sobrante'] = ''
        conciliar['Observaciones'] = ''
        conciliar['Valor a afectar por PyG de No calidad'] = ''
        conciliar['Observaciones reclamos'] = ''
        conciliar['Código Sucursal'] = ''
        conciliar['DNE ATASCOS'] = np.where(conciliar['cuenta_contable'] == 199095144, 'atascos', 'DNE')
        conciliar['VALIDACIÓN'] = 'CORRECTO'

        # seleccionamos solo columnas necesarias
        cols = ['Fecha Abono', 'Cédula', 'Cajero', 'Transportadora', 'Transacción', 'Fecha Transacción', 
            'Número De Tarjeta', 'Error', 'Valor De La Transacción', 'Valor abonado al Cliente', 
            'Número De Cuenta', 'OBSERVACIONES', 'Código de Oficina', 'Nro. Sucursal', 'FECHA DE RADICACION', 
            'Segmento', 'Nro. Radicado', 'Fecha reclamo sistema (AAAAMMDD)', 'Código Sucursal', 
            'Valor transferido a la cuenta temporal de reclamos', 'Fecha de Sobrante', 'Observaciones', 
            'Valor a afectar por PyG de No calidad', 'Observaciones reclamos', 'DNE ATASCOS', 'VALIDACIÓN',
            'fecha_envio_para_conciliacion', 'fecha_conciliacion'] 

        conciliar = conciliar[cols].copy()

        # guardar en historico
        ruta_hist_conc = self.params['carpeta_ppal'] \
            + 'conciliacion/para_conciliar/historico_conciliar.xlsx'

        historico_conciliar = pandas.read_excel(ruta_hist_conc)

        historico_conciliar = historico_conciliar.append(conciliar, ignore_index=True)

        # verificar para partir cada 6 meses
        historico_conciliar.loc[historico_conciliar['fecha_conciliacion'] == '', 'fecha_conciliacion'] = np.nan

        max_fecha = historico_conciliar.loc[
            historico_conciliar['fecha_conciliacion'].notnull(), 'fecha_conciliacion'].max()
        min_fecha = historico_conciliar.loc[
            historico_conciliar['fecha_conciliacion'].notnull(), 'fecha_conciliacion'].min()

        if not pandas.isna(max_fecha) and not pandas.isna(min_fecha) and (max_fecha - min_fecha).days >= 180:
            fecha_part = min_fecha + datetime.timedelta(days=180)

            cond = historico_conciliar['fecha_conciliacion'] <= fecha_part
            nueva_part = historico_conciliar[cond].copy()
            historico_conciliar = historico_conciliar[~cond].copy()

            max_fecha_part = nueva_part['fecha_conciliacion'].max()
            min_fecha_part = nueva_part['fecha_conciliacion'].min()

            # guardamos particion
            nueva_part.to_excel(self.params['carpeta_ppal'] \
                + f'conciliacion/para_conciliar/historico_conciliar_part_\
                {max_fecha_part.strftime("%Y%m%d")}_{min_fecha_part.strftime("%Y%m%d")}.xlsx',
                index=None)

            print('Info: Se ha creado una particion de 6 meses en el archivo historico de abonos para conciliar')

        # guardamos historico para conciliar
        historico_conciliar.to_excel(ruta_hist_conc, index=None)

        # guardar historico editado y en checkpoints
        reclamos.to_excel(self.params['carpeta_ppal'] \
            + 'conciliacion/historico_reclamos_pendientes.xlsx', index=None)

        ruta_checkpoints = self.params['carpeta_ppal'] \
            + f'conciliacion/checkpoints/{self.fecha.strftime("%Y%m%d")}/'

        if os.path.exists(ruta_checkpoints):

            reclamos.to_excel(f'{ruta_checkpoints}historico_reclamos_pendientes.xlsx', index=None)

        # mensaje informativo
        print('Info: Se edito de manera exitosa el archivo de historico de reclamos pendientes')
        print('Info: Se guardo existosamente el historico de abonos para conciliar')

        # # # # # Revisar lo de cancelacion correo


    def guardar_reporte_reclamos(self, dne, mf):

        fila_ini = 4
        ruta_plantilla =  self.params['carpeta_plantilla'] \
            + 'plantilla_reporte_reclamos.xlsx'

        plantilla = openpyxl.load_workbook(
            filename=ruta_plantilla)
 
        mf_hoja = plantilla['MF DETALLE']
        dne_hoja = plantilla['DNE DETALLE']
        resumen_hoja = plantilla['RESUMEN']

        cols_datos = ['Observaciones', 'Cod Ofna.', 'Fecha', 
            'Tercero', 'Monto', 'Radicado', 'Número de cuenta']

        cols_excel = [chr(ord('B') + i) for i in range(7)]

        # llenamos dne
        for i, row in zip(dne.index, range(fila_ini, fila_ini + dne.shape[0])):
            
            for col_datos, col_excel in zip(cols_datos, cols_excel):
                dne_hoja[f'{col_excel}{row}'] = dne.loc[i, col_datos]

        # llenamos mf
        for i, row in zip(mf.index, range(fila_ini, fila_ini + mf.shape[0])):
            
            for col_datos, col_excel in zip(cols_datos, cols_excel):
                mf_hoja[f'{col_excel}{row}'] = mf.loc[i, col_datos]


        # hacemos agrupacion para resumen
        grupo_mf = mf.set_index('Fecha')
        grupo_mf_cinfo = grupo_mf[grupo_mf['Observaciones'].notnull()].groupby(pandas.Grouper(freq='M'))
        grupo_mf_sinfo = grupo_mf[grupo_mf['Observaciones'].isnull()].groupby(pandas.Grouper(freq='M'))

        grupo_mf_cinfo = grupo_mf_cinfo.agg({
            'Cod Ofna.': 'count',
            'Monto': 'sum'
        })

        grupo_mf_sinfo = grupo_mf_sinfo.agg({
            'Cod Ofna.': 'count',
            'Monto': 'sum'
        })

        grupo_mf_cinfo.reset_index(inplace=True)
        grupo_mf_sinfo.reset_index(inplace=True)

        grupo_mf_cinfo.rename(columns={
            'Cod Ofna.': 'numero_con_info',
            'Monto': 'monto_con_info'
        }, inplace=True)

        grupo_mf_sinfo.rename(columns={
            'Cod Ofna.': 'numero_sin_info',
            'Monto': 'monto_sin_info'
        }, inplace=True)

        grupo_mf = grupo_mf_sinfo.merge(grupo_mf_cinfo, on='Fecha', how='outer')

        grupo_mf['tipo'] = 'MF'
        grupo_mf['Fecha'] = grupo_mf['Fecha'].dt.strftime('%Y-%m')

        # hacemos agrupacion para resumen
        grupo_dne = dne.set_index('Fecha')
        grupo_dne_cinfo = grupo_dne[grupo_dne['Observaciones'].notnull()].groupby(pandas.Grouper(freq='M'))
        grupo_dne_sinfo = grupo_dne[grupo_dne['Observaciones'].isnull()].groupby(pandas.Grouper(freq='M'))

        grupo_dne_cinfo = grupo_dne_cinfo.agg({
            'Cod Ofna.': 'count',
            'Monto': 'sum'
        })

        grupo_dne_sinfo = grupo_dne_sinfo.agg({
            'Cod Ofna.': 'count',
            'Monto': 'sum'
        })

        grupo_dne_cinfo.reset_index(inplace=True)
        grupo_dne_sinfo.reset_index(inplace=True)

        grupo_dne_cinfo.rename(columns={
            'Cod Ofna.': 'numero_con_info',
            'Monto': 'monto_con_info'
        }, inplace=True)

        grupo_dne_sinfo.rename(columns={
            'Cod Ofna.': 'numero_sin_info',
            'Monto': 'monto_sin_info'
        }, inplace=True)

        grupo_dne = grupo_dne_sinfo.merge(grupo_dne_cinfo, on='Fecha', how='outer')

        grupo_dne['tipo'] = 'DNE'
        grupo_dne['Fecha'] = grupo_dne['Fecha'].dt.strftime('%Y-%m')

        resumen = grupo_dne.append(grupo_mf, ignore_index=True)

        # llenar hoja de resumen
        cols_excel = [chr(ord('B') + i) for i in range(6)]
        cols_datos = resumen.columns.tolist()

        # llenamos resumen
        for i, row in zip(resumen.index, range(fila_ini, fila_ini + resumen.shape[0])):
            
            for col_datos, col_excel in zip(cols_datos, cols_excel):
                resumen_hoja[f'{col_excel}{row}'] = resumen.loc[i, col_datos]
        
        # guardar
        nombre_salida = self.params['carpeta_ppal'] \
            + f'conciliacion/reporte_reclamos/reporte_reclamos_{self.fecha.strftime("%Y%m%d")}.xlsx'
        plantilla.save(nombre_salida)



    def generar_reporte_para_reclamos(self):

        # leer reclamos pendientes
        reclamos = self.insumos.leer_excel('reclamos')

        # leer rango de fechas
        fecha_ini, fecha_fin = self.params['rango_fechas']
        
        # print(f"\nrango_fechas: {fecha_ini} - {fecha_fin}\n")

        # leer partidas devueltas en ese rango de fecha
        partidas_devueltas = []

        fecha_aux = fecha_ini 

        while fecha_aux != fecha_fin + datetime.timedelta(days=1):

            ruta_partidas_devolver = self.params['carpeta_ppal'] \
                + f'conciliacion/partidas_devolver/partidas_devolver_{fecha_aux.strftime("%Y%m%d")}.xlsx' 

            if os.path.exists(ruta_partidas_devolver):
                partidas_devueltas += [pandas.read_excel(ruta_partidas_devolver)]

            fecha_aux = fecha_aux + datetime.timedelta(days=1)

        partidas_devueltas = pandas.concat(partidas_devueltas, ignore_index=True)
        # partidas_devueltas.to_excel('partidas_devueltas_pruebas.xlsx', index=False)

        # filtrar partidas devueltas
        # cols = ['nit', 'radicado', 'valor', 'archivo_fuente', 'dne_mf', 'causa_devolucion']
        cols = ['nit', 'radicado', 'valor', 'archivo_fuente', 'causa_devolucion']

        partidas_devueltas = partidas_devueltas[cols]

        # filtrar reclamos
        reclamos = reclamos[
            (reclamos['estado_cruce'] == 'SIN CRUZAR')
            & (reclamos['naturaleza'] == 'DB')].copy()

        # cruzar partidas devueltas con pendientes
        total = reclamos.merge(partidas_devueltas, on=['nit', 'radicado', 'valor'], how='left')


        # formateamos total
        cols = ['causa_devolucion', 'oficina_cuenta_contable', 'fecha', 'nit', 
            'valor', 'radicado', 'cuenta_cliente', 'cuenta_contable']

        total = total[cols]
        total.rename(columns={
            'causa_devolucion': 'Observaciones',
            'oficina_cuenta_contable': 'Cod Ofna.',
            'fecha': 'Fecha',
            'nit': 'Tercero',
            'valor': 'Monto',
            'radicado': 'Radicado',
            'cuenta_cliente': 'Número de cuenta'
        }, inplace=True)

        # partimos en multis y dne
        total_mf = total[total['cuenta_contable'] == 199095144].copy()
        total_dne = total[total['cuenta_contable'] == 199095096].copy()

        total_mf.drop('cuenta_contable', axis=1, inplace=True)
        total_dne.drop('cuenta_contable', axis=1, inplace=True)

        # borramos repetidas
        total_mf.drop_duplicates(['Tercero', 'Monto', 'Radicado'], inplace=True)
        total_dne.drop_duplicates(['Tercero', 'Monto', 'Radicado'], inplace=True)

        # generar reporte y guardar con fecha de creacion
        self.guardar_reporte_reclamos(total_dne, total_mf)

        print('Info: Reporte para reclamos generado con exito!')

        #total.to_excel(self.params['carpeta_ppal'] \
        #    + f'conciliacion/reporte_reclamos/reporte_reclamos_{self.fecha.strftime("%Y%m%d")}.xlsx')