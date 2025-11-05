import datetime

import pandas
import numpy as np

from utilidades.admin_excel import AdminExcel
from utilidades.operaciones_pandas import reducir


class AdminInsumos(AdminExcel):

    def __init__(self, lista_archivos):

        super().__init__(lista_archivos)


    def formatear_fecha(self, fecha):

        if isinstance(fecha, datetime.datetime) or \
            isinstance(fecha, datetime.date):
            return fecha

        aux_fecha = str(fecha)

        if len(aux_fecha) < 6:
            excel_fecha = 44428
            segundos = (excel_fecha - 25569)*86400.0
            aux_fecha = datetime.datetime.utcfromtimestamp(segundos)

        elif aux_fecha.startswith('20') and aux_fecha[2] not in ['0', '1'] and len(aux_fecha) == 8:
            aux_fecha = datetime.datetime.strptime(aux_fecha, '%Y%m%d')

        elif aux_fecha[-4:-2] == '20' and aux_fecha[-2] not in ['0', '1']: 
            if '/' in aux_fecha: aux_fecha = aux_fecha.replace('/', '')
            if len(aux_fecha) == 7: aux_fecha = '0' + aux_fecha 

            aux_fecha = datetime.datetime.strptime(aux_fecha, '%d%m%Y')

        else:
            print(aux_fecha)
            import sys 
            sys.exit()

        return aux_fecha
            
    
    def config_reclamos(self, df):

        df = df.copy()

        return df


    def config_requerimientos_nequi(self, df):

        cols = ['Nit Reclamo', 'Radicado reclamo', 'VALOR ABONADO POR CAJEROS', 
            'Tipología SAP CRM', 'Valor De La Transacción', 'Código del  Cajero', 
            'Transacción', 'Fecha Transacción', 'Error / Tira Auditoria', 'FECHA ABONO', 
            'Fecha Solicitud']

        df.columns = [i.replace('\n', '').strip().replace('\xa0', ' ') for i in df.columns]
        
        df = df[cols].copy()

        df.rename(columns={
            'Nit Reclamo': 'nit',
            'Radicado reclamo': 'radicado',
            'VALOR ABONADO POR CAJEROS': 'valor',
            'Tipología SAP CRM': 'observaciones',
            'Valor De La Transacción': 'valor_trxn',
            'Código del  Cajero': 'codigo_cajero',
            'Transacción': 'codigo_trxn',
            'Fecha Transacción': 'fecha_trxn',
            'Error / Tira Auditoria': 'tira_trxn', 
            'FECHA ABONO': 'fecha_abono',
            'Fecha Solicitud': 'fecha_creacion'
        }, inplace=True)

        df = df[df['nit'].notnull()].copy()

        # formateamos fechas
        df['fecha_trxn'] = pandas.to_datetime(df['fecha_trxn'], format='%Y-%m-%d')
        df['fecha_abono'] = pandas.to_datetime(df['fecha_abono'], format='%Y-%m-%d')
        df['fecha_creacion'] = pandas.to_datetime(df['fecha_creacion'])

        return df 

    def config_otras_redes(self, df):

        cols = ['Nit Reclamo', 'Radicado reclamo', 'VALOR ABONADO POR CAJEROS', 
            'Tipología SAP CRM', 'Valor De La Transacción', 'Código del  Cajero', 
            'Transacción', 'Fecha Transacción', 'Error / Tira Auditoria', 'FECHA ABONO', 
            'Fecha Solicitud']

        df.columns = [i.replace('\n', '').strip().replace('\xa0', ' ') for i in df.columns]
        
        df = df[cols].copy()

        df.rename(columns={
            'Nit Reclamo': 'nit',
            'Radicado reclamo': 'radicado',
            'VALOR ABONADO POR CAJEROS': 'valor',
            'Tipología SAP CRM': 'observaciones',
            'Valor De La Transacción': 'valor_trxn',
            'Código del  Cajero': 'codigo_cajero',
            'Transacción': 'codigo_trxn',
            'Fecha Transacción': 'fecha_trxn',
            'Error / Tira Auditoria': 'tira_trxn', 
            'FECHA ABONO': 'fecha_abono',
            'Fecha Solicitud': 'fecha_creacion'
        }, inplace=True)

        #df.to_excel('df_config_otras_redes.xlsx', index=False)

        #df = df[df['nit'].notnull()].copy()

        # formateamos fechas
        df['fecha_trxn'] = pandas.to_datetime(df['fecha_trxn'], format='%Y-%m-%d')
        df['fecha_abono'] = pandas.to_datetime(df['fecha_abono'], format='%Y-%m-%d')
        df['fecha_creacion'] = pandas.to_datetime(df['fecha_creacion'])

        return df

    def config_tarjetas_propias(self, df):

        cols = ['Nit Reclamo', 'Radicado reclamo', 'VALOR ABONADO POR CAJEROS', 
            'Tipología SAP CRM', 'Valor de la transacción', 'Código del  Cajero', 
            'Transacción', 'Fecha Transacción', 'Error / Tira Auditoria', 'FECHA ABONO', 
            'Fecha Solicitud']

        df.columns = [i.replace('\n', '').strip().replace('\xa0', ' ') for i in df.columns]
        
        df = df[cols].copy()

        df.rename(columns={
            'Nit Reclamo': 'nit',
            'Radicado reclamo': 'radicado',
            'VALOR ABONADO POR CAJEROS': 'valor',
            'Tipología SAP CRM': 'observaciones',
            'Valor de la transacción': 'valor_trxn',
            'Código del  Cajero': 'codigo_cajero',
            'Transacción': 'codigo_trxn',
            'Fecha Transacción': 'fecha_trxn',
            'Error / Tira Auditoria': 'tira_trxn', 
            'FECHA ABONO': 'fecha_abono',
            'Fecha Solicitud': 'fecha_creacion'
        }, inplace=True)

        #df = df[df['nit'].notnull()].copy()

        # formateamos fechas
        df['fecha_trxn'] = pandas.to_datetime(df['fecha_trxn'], format='%Y-%m-%d')
        df['fecha_abono'] = pandas.to_datetime(df['fecha_abono'], format='%Y-%m-%d')
        df['fecha_creacion'] = pandas.to_datetime(df['fecha_creacion'])

        return df  

    def config_cajeros_produccion(self, df):

        cols = ['CODIGO', 'Dispensador / Multifuncional', 'COD. SUC', 'ADMINISTRACIÓN']
        
        df = df[cols].copy()
        df.columns = self.config['cols']

        df = df[df['codigo_cajero'].notnull()].copy()

        return df







        
