import sys
import getpass


class AdminPassword():
    
    def __init__(self, params):
        self.params = params
    
    
    def __es_llave_usuario(self, llave):
        if 'usuario' in llave:
            return True
        
        return False
        

    def __obtener_llaves_usuarios(self):
        if isinstance(self.params, dict):
            llaves = self.params.keys()
            llaves_usuario_iterador = filter(self.__es_llave_usuario, llaves)
            llaves_usuario = list(llaves_usuario_iterador)
            
            return llaves_usuario
        
        else:
            return None
        
    
    def __solicitar_passw(self, tipo):
        
        if tipo == 'med':
            llave = 'clave_med'
            valor = getpass.getpass(prompt='>> password medellin: ')    
        elif tipo == 'nal':
            llave = 'clave_nal'
            valor = getpass.getpass(prompt='>> password nacional: ')
        elif tipo == 'lz':
            llave = 'clave_lz'
            valor = getpass.getpass(prompt='>> password lz: ')
        
        print("\n")
        
        return llave, valor
    
    
    def __agregar_clave_dict(self, clave, valor):
        self.params[clave] = valor
    
        
    def obtener_passw_usuarios(self):
        llaves_usuarios = self.__obtener_llaves_usuarios()
        
        print("\nPor favor digitar password requerido: \n")
        
        for llave_usuario in llaves_usuarios:
            if 'med' in llave_usuario:
                llave, valor = self.__solicitar_passw(tipo='med')
                self.__agregar_clave_dict(llave, valor)
            elif 'nal' in llave_usuario:
                llave, valor = self.__solicitar_passw(tipo='nal')
                self.__agregar_clave_dict(llave, valor)
            elif 'lz' in llave_usuario:
                llave, valor = self.__solicitar_passw(tipo='lz')
                self.__agregar_clave_dict(llave, valor)
                
        return self.params