import win32com.client as win32


class AdminEmails(object):

    def __init__(self):
        self.outlook = win32.Dispatch('outlook.application')


    def enviar_email(self, emails, asunto, cuerpo, ruta_archivos=None, copias=None):

        mail = self.outlook.CreateItem(0)

        if isinstance(emails, list):
            mail.To = emails[0]
        
            for i in emails[1:]:
                mail.Recipients.Add(i)

        else: 
            mail.To = emails
            
        mail.Subject = asunto
        mail.HTMLBody = cuerpo
        
        if copias:    
            if isinstance(copias, list):
                emails_cc = ';'.join(copias)
                mail.cc = emails_cc
            else:
                mail.cc = copias

        if ruta_archivos:
            for i in ruta_archivos:
                mail.Attachments.Add(Source=i)
                
        mail.Send()