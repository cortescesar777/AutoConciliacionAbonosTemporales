import pyodbc
import pandas

class AdminBD(object):

    def __init__(self, servidor, usuario, clave):
        
        self.servidor = servidor
        self.usuario = usuario 
        self.clave = clave


    def conectar(self):
        self.conn = pyodbc.connect(f'''
            DSN={self.servidor}; 
            CCSID=37; 
            TRANSLATE=1; 
            UID={self.usuario}; 
            PWD={self.clave}''')

        return self.conn


    def consultar(self, consulta):
        self.conectar()
        df = pandas.read_sql(consulta, self.conn)
        return df


class AdminBDMedellin(AdminBD):

    def __init__(self, usuario, clave):
        super().__init__('MEDELLIN', usuario, clave)



class AdminBDNacional(AdminBD):

    def __init__(self, usuario, clave):
        super().__init__('NACIONAL', usuario, clave)



class AdminBDLZ(AdminBD):

    def __init__(self, usuario, clave):
        super().__init__('LZ', usuario, clave)


    def conectar(self):

        self.conn = pyodbc.connect('DSN=IMPALA_PROD', autocommit=True)

        return self.conn