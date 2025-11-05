import time
import datetime

import schedule


class AdminSchedule(object):

    def __init__(self):
        pass

    def calendarizar(self, f, rango_horas, freq_min):
        
        hora_inicio = rango_horas[0]
        hora_fin = rango_horas[1]

        hora_contador, i = hora_inicio.strftime('%H:%M'), 0

        while hora_contador != hora_fin.strftime('%H:%M'):

            hora_contador = (hora_inicio 
                + datetime.timedelta(minutes=freq_min*i)).strftime('%H:%M')
            schedule.every().day.at(hora_contador).do(f)

            i += 1

        print('Info: Todo ajustado y pendiente para ejecución')

        while True:
            schedule.run_pending()
            time.sleep(1)

        

