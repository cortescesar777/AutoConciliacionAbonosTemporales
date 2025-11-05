
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext


class AdminSharepointLists(object):


    def __init__(self, url, usuario, clave):

        self.usuario = usuario 
        self.clave = clave 

        self.url = url


    def conectar(self):
        
        self.ctx = ClientContext(self.url).with_credentials(
            UserCredential(self.usuario, self.clave))
        self.web = self.ctx.web

        return self.web, self.ctx


    def obtener_lista(self, nombre_lista):

        self.conectar()

        lista_sharepoint = self.web.lists.get_by_title(nombre_lista)

        items = lista_sharepoint.get_items()

        self.ctx.load(items)
        self.ctx.execute_query()

        return items


    def subir_registros_sharepoint(self, nombre_lista, registros):

        self.conectar()

        lista_sharepoint = self.web.lists.get_by_title(nombre_lista)

        cols_regs = registros.columns

        for i in registros.index:

            item = {'Title': str(i)}

            item.update({
                col_reg: registros.loc[i, col_reg] 
                for col_reg in cols_regs})

            lista_sharepoint.add_item(item)

        self.ctx.execute_query()

        return True