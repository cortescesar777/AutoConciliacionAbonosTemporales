import sys
from utilidades.admin_excel import AdminExcel


class AdminInsumos(AdminExcel):

    def __init__(self, lista_archivos):

        super().__init__(lista_archivos)

    
    def config_historico_batch(self, df):
        
        df = df[['NUMERO DE CUENTA', 'N° DE TRANSACCION', 'Fecha Proceso', 'VALOR']].copy()
        df.columns = ['numero_cuenta', 'codigo_trxn', 'fecha_proceso', 'valor_trxn']

        #df['valor_trxn'] = df['valor_trxn'].astype(int)

        return df