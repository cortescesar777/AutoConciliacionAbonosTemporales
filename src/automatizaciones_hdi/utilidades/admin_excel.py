import sys 
import os

import pandas

class AdminExcel(object):

    def __init__(self, lista_archivos):

        self.lista_archivos = lista_archivos


    def leer_multiples_excel(self, ids):

        r = [self.leer_excel(i) for i in ids]

        return r


    def guardar_excel(self, df, id_archivo=None, config=None):
        
        if not config and id_archivo:
            config = [i for i in self.lista_archivos 
                        if i['id_archivo'] == id_archivo]
            
            if not config:
                print(f'Error: {id_archivo} archivo no existe, ' 
                'verifique su archivo de configuracion')
                sys.exit()
            else: 
                config = config[0]

            
        df.to_excel(
            config['ruta_archivo_salida'],
            index=config.get('index', None),
            sheet_name=config.get('nombre_hoja_salida', 'Sheet1'))
        
        
    def leer_excel(self, id_archivo, columnas_str=None, config=None):

        self.id_archivo = id_archivo

        if not config:
            self.config = [i for i in self.lista_archivos if i['id_archivo'] == self.id_archivo]
            
            if not self.config:  
                print(f'Error: {id_archivo} archivo no existe, ' 
                    'verifique su archivo de configuracion')
                sys.exit()
            else: 
                self.config = self.config[0]


        if os.path.exists(self.config['ruta_archivo']):
            
            if '.xls' in self.config['ruta_archivo']:
                if columnas_str is not None:
                    df = pandas.read_excel(
                        self.config['ruta_archivo'], 
                        sheet_name=self.config.get('nombre_hoja', 0),
                        engine=self.config.get('motor', None),
                        dtype={col: str for col in columnas_str})
                else:
                    df = pandas.read_excel(
                        self.config['ruta_archivo'], 
                        sheet_name=self.config.get('nombre_hoja', 0),
                        engine=self.config.get('motor', None))
                    
            elif '.csv' in self.config['ruta_archivo']:
                df = pandas.read_csv(self.config['ruta_archivo'])

        else:
            print(f'Error: {self.config["ruta_archivo"]} no existe')
            sys.exit()

        df = eval(f'self.config_{self.config["id_archivo"]}(df)')

        return df
    
    
    def guardar_multiples_hojas_excel(self, list_df, list_sheets=None, id_archivo=None, config=None):
        if not config and id_archivo:
            config = [i for i in self.lista_archivos 
                        if i['id_archivo'] == id_archivo]
            
            if not config:
                print(f'Error: {id_archivo} archivo no existe, ' 
                'verifique su archivo de configuracion')
                sys.exit()
            else: 
                config = config[0]
                
        if len(list_df) == len(list_sheets):
            with pandas.ExcelWriter(config['ruta_archivo_salida']) as writer:
                for i in range(0, len(list_df)):
                    list_df[i].to_excel(writer, sheet_name=list_sheets[i], index=False)
        else:
            print("Revise la lista de dataframes y hojas")