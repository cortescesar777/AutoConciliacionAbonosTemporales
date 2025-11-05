
import sys
import os
import yaml 


RUTA_CONFIG_DEV = sys.argv[1]
RUTA_TAREAS = sys.argv[2]
TAREA = sys.argv[3]


with open(RUTA_CONFIG_DEV, encoding='utf-8') as f:
    CONFIG_DEV = yaml.safe_load(f)

with open(RUTA_TAREAS, encoding='utf-8') as f:
    TAREAS = yaml.safe_load(f)

PROYECTOS = [i['proyecto'] for i in CONFIG_DEV]


def obtener_nombre_proyecto():
    
    params = [i for i in TAREAS if i['tarea'] == TAREA]

    if len(params) == 0:
        print('Error: tarea no existe, revise su archivo de tareas')
        sys.exit()

    params = params[0]

    config = [i for i in CONFIG_DEV if i['proyecto'] == params['proyecto']]

    if len(config) == 0:
        print('Error: la configuracion para este proyecto no existe')
        print(CONFIG_DEV)
        print(params['proyecto'])
        sys.exit()

    nombre_proyecto = config[0]['proyecto'].split('_')
    nombre_proyecto = [i.capitalize() for i in nombre_proyecto]
    nombre_proyecto = ' '.join(nombre_proyecto)

    return nombre_proyecto


def obtener_parametros_insumos():
    params = [i for i in TAREAS if i['tarea'] == TAREA]

    if len(params) == 0:
        print('Error: tarea no existe, revise su archivo de tareas')
        sys.exit()
    
    params = params[0]

    config = [i for i in CONFIG_DEV if i['proyecto'] == params['proyecto']]

    if len(config) == 0:
        print('Error: la configuracion para este proyecto no existe')
        sys.exit()

    config = config[0]['insumos']

    proyecto = params['proyecto']
    proyecto = [i.capitalize() for i in proyecto.split('_')]
    proyecto = ''.join(proyecto)
    
    funcion = TAREA.split(params['proyecto'] + '_')[1]
    
    objeto_tarea = eval(f'{proyecto}(params, config)')
    salida = eval(f'objeto_tarea.{funcion}()')

    return salida


if 'cuadre_cajeros_sucursales' in PROYECTOS:
    from proyectos.vneg_cuadre_cajeros_sucursales.cuadre_cajeros_sucursales import CuadreCajerosSucursales
    
if 'pagado_por_hora' in PROYECTOS:
    from proyectos.pagado_por_hora.pagado_por_hora import PagadoPorHora
    
if 'pagado_por_hora_contingencia' in PROYECTOS:
    from proyectos.pagado_por_hora_contingencia.pagado_por_hora_contingencia import PagadoPorHoraContingencia

if 'control_cajas_recaudadoras' in PROYECTOS:
    from proyectos.control_cajas_recaudadoras.control_cajas_recaudadoras import ControlCajasRecaudadoras

if 'cuadre_cajeros_suc' in PROYECTOS:
    from proyectos.cuadre_cajeros_suc.cuadre_cajeros_suc import CuadreCajerosSuc

if 'conciliacion_reclamos' in PROYECTOS:
    from proyectos.conciliacion_reclamos.conciliacion_reclamos import ConciliacionReclamos

if 'cuadre_remanentes_multis' in PROYECTOS:
    from proyectos.cuadre_remanentes_multis.cuadre_remanentes_multis import CuadreRemanentesMultis

if 'prueba_reclamos' in PROYECTOS: 
    from proyectos.prueba_reclamos.conciliacion_reclamos import PruebaConciliacionReclamos

if 'cuadre_cuenta_062' in PROYECTOS:
    from proyectos.cuadre_cuenta_062.cuadre_cuenta_062 import CuadreCuenta062

# if 'notificaciones_faltantes_suc' in PROYECTOS:
#     from proyectos.notificaciones_faltantes_suc.notificaciones_faltantes_suc import NotificacionesFaltantesSuc

if 'filtros_partidas_reclamos' in PROYECTOS:
    from proyectos.filtros_partidas_reclamos.filtros_partidas_reclamos import FiltrosPartidasReclamos

if 'punteo_cajeros_dispensadores' in PROYECTOS:
    from proyectos.punteo_cajeros_dispensadores.punteo_cajeros_dispensadores import PunteoCajerosDispensadores

if 'reporte_sucs_indisponibilidad' in PROYECTOS:
    from proyectos.reporte_sucs_indisponibilidad.reportes_sucs_indisponibilidad import ReporteSucsIndisponibilidad

if 'cuadre_cajeros_tdv' in PROYECTOS:
    from proyectos.cuadre_cajeros_tdv.cuadre_cajeros_tdv import CuadreCajerosTdv
    
if 'cabffanti_diario' in PROYECTOS:
    from proyectos.cabffanti_diario.cabffanti_diario import CabffantiDiario
    
if 'estado_cuentas_gsef' in PROYECTOS:
    from proyectos.estado_cuentas_gsef.estado_cuentas_gsef import EstadoCuentasGsef
    
if 'bajas_denominaciones' in PROYECTOS:
    from proyectos.bajas_denominaciones.bajas_denominaciones import BajasDenominaciones
    
if 'cuentas_gsef_diario' in PROYECTOS:
    from proyectos.vneg_cuentas_gsef_diario.cuentas_gsef_diario import CuentasGsefDiario

if 'Combos_Canales_Fisicos' in PROYECTOS:
    from proyectos.Combos_Canales_Fisicos.Combos_Canales_Fisicos import CombosCanalesFisicos

if 'Combos_Actualizar_Cb' in PROYECTOS:
    from proyectos.Combos_Actualizar_Cb.Combos_Actualizar_Cb import CombosActualizarCb
    
if 'proyecto_arqueos_cajeros_suc' in PROYECTOS:
    from proyectos.arqueos_cajeros_sucursales.proyecto_arqueos_cajeros_suc import ProyectoArqueosCajerosSuc

if 'cajeros_agotados_reincidentes' in PROYECTOS:
    from proyectos.cajeros_agotados_reincidentes.cajeros_agotados_reincidentes import CajerosAgotadosReincidentes

if 'altas_denominaciones' in PROYECTOS:
    from proyectos.altas_denominaciones.altas_denominaciones import AltasDenominaciones

if 'insumos_simetrik_redeban_credibanco' in PROYECTOS:
    from proyectos.insumos_simetrik_redeban_credibanco.insumos_simetrik_redeban_credibanco import InsumosSimetrikRedebanCredibanco

if 'traslados_entre_fondos' in PROYECTOS:
    from proyectos.traslados_entre_fondos.traslados_entre_fondos import TrasladosEntreFondos
    
if 'traslados_entre_fondos_y_grabar' in PROYECTOS:
    from proyectos.traslados_entre_fondos_y_grabar.traslados_entre_fondos_y_grabar import TrasladosEntreFondosYGrabar
    
if 'envio_cartas_atm_pruebas' in PROYECTOS:
    from proyectos.envio_cartas_atm_pruebas.envio_cartas_atm_pruebas import EnvioCartasAtmPruebas

if 'envio_cartas_atm' in PROYECTOS:
    from proyectos.envio_cartas_atm.envio_cartas_atm import EnvioCartasAtm
    
if 'grabar_novedades_brinks' in PROYECTOS:
    from proyectos.vneg_grabar_novedades_brinks.grabar_novedades_brinks \
        import GrabarNovedadesBrinks
    
if 'disponibles_para_venta_alta' in PROYECTOS:
    from proyectos.disponibles_para_venta_alta.disponibles_para_venta_alta \
        import DisponiblesParaVentaAlta
             
if 'punteo_dispensadores_ciclo' in PROYECTOS:
    from proyectos.vneg_punteo_dispensadores_ciclo.punteo_dispensadores_ciclo \
        import PunteoDispensadoresCiclo
        
if 'generador_pedidos_insumos' in PROYECTOS:
    from proyectos.vneg_generador_pedidos_insumos.generador_pedidos_insumos   \
        import GeneradorPedidosInsumos

if 'generar_plano_brinks' in PROYECTOS:
    from proyectos.generar_plano_brinks.generar_plano_brinks import GenerarPlanoBrinks

if 'reclamos_nq_tj_or' in PROYECTOS:
    from proyectos.reclamos_nq_tj_or.reclamos_nq_tj_or import ReclamosNqTjOr
    
if 'flujo_aprobaciones_cajas' in PROYECTOS:
    from proyectos.flujo_aprobaciones_cajas.flujo_aprobaciones_cajas import FlujoAprobacionesCajas
    
if 'flujo_revision_cajas' in PROYECTOS:
    from proyectos.flujo_revision_cajas.flujo_revision_cajas import FlujoRevisionCajas

if 'informe_estado_dolares' in PROYECTOS:
    from proyectos.informe_estado_dolares.informe_estado_dolares import InformeEstadoDolares

if 'control_cajas_recaudadoras_informe' in PROYECTOS:
    from proyectos.control_cajas_recaudadoras_informe.control_cajas_recaudadoras_informe import ControlCajasRecaudadorasInforme
    
if 'conciliacion_cuenta_caja_sucursales' in PROYECTOS:
    from proyectos.vneg_conciliacion_cuenta_caja_sucursales.conciliacion_cuenta_caja_sucursales   \
        import ConciliacionCuentaCajaSucursales
        
if 'legalizar_recolecciones_sucursales' in PROYECTOS:
    from proyectos.vneg_legalizar_recolecciones_sucursales.legalizar_recolecciones_sucursales   \
        import LegalizarRecoleccionesSucursales
        
if 'conciliacion_reclamos_sobrantes_atms' in PROYECTOS:
    from proyectos.vneg_conciliacion_reclamos_sobrantes_atms.conciliacion_reclamos_sobrantes_atms \
        import ConciliacionReclamosSobrantesAtms
        
if 'vneg_conciliacion_fondos_plandechoque' in PROYECTOS:
    from proyectos.vneg_conciliacion_fondos_plandechoque.vneg_conciliacion_fondos_plandechoque \
        import VnegConciliacionFondosPlandechoque
        
if 'grabar_ventas_efectivo' in PROYECTOS:
    from proyectos.vneg_grabar_ventas_efectivo.grabar_ventas_efectivo \
        import GrabarVentasEfectivo    
        
if 'consulta_saldos_finales_fondos' in PROYECTOS:
    from proyectos.vneg_consulta_saldos_finales_fondos.consulta_saldos_finales_fondos \
        import ConsultaSaldosFinalesFondos
        
if 'tasas_venta_alta' in PROYECTOS:
    from proyectos.tasas_venta_alta.tasas_venta_alta \
        import TasasVentaAlta
    
if 'informe_saldos_cajas_diarios' in PROYECTOS:
    from proyectos.vneg_informe_saldos_cajas_diarios.informe_saldos_cajas_diarios \
        import InformeSaldosCajasDiarios
        
if 'validacion_pagos_automaticos' in PROYECTOS:
    from proyectos.validacion_pagos_automaticos.validacion_pagos_automaticos \
        import ValidacionPagosAutomaticos

if 'grabar_pagos_clientes' in PROYECTOS:
    from proyectos.vneg_grabar_pagos_clientes.grabar_pagos_clientes \
        import GrabarPagosClientes
        
if 'convertir_fajillas' in PROYECTOS:
    from proyectos.convertir_fajillas.convertir_fajillas \
        import ConvertirFajillas
        
if 'validacion_cartas_venta_de_alta' in PROYECTOS:
    from proyectos.validacion_cartas_venta_de_alta.validacion_cartas_venta_de_alta \
        import ValidacionCartasVentaDeAlta
        
if 'alertas_extracupos' in PROYECTOS:
    from proyectos.alertas_extracupos.alertas_extracupos \
        import AlertasExtracupos

if 'grabar_operacionesbr_traslados' in PROYECTOS:
    from proyectos.vneg_grabar_operacionesbr_traslados.grabar_operacionesbr_traslados \
        import GrabarOperacionesbrTraslados

if 'informe_saldos_cajas_diarios_calendarizado' in PROYECTOS:
    from proyectos.vneg_informe_saldos_cajas_diarios.informe_saldos_cajas_diarios_calendarizado \
        import InformeSaldosCajasDiariosCalendarizado
        
if 'almacenamiento_efectivo_tdv' in PROYECTOS:
    from proyectos.gselef_almacenamiento_efectivo_tdv.almacenamiento_efectivo_tdv \
        import AlmacenamientoEfectivoTdv
        
if 'facturacion_cajeros' in PROYECTOS:
    from proyectos.gselef_facturacion_cajeros.facturacion_cajeros \
        import FacturacionCajeros

if 'insumos_conciliacion_comisiones_redeban' in PROYECTOS:
    from proyectos.insumos_conciliacion_comisiones_redeban.insumos_conciliacion_comisiones_redeban \
        import InsumosConciliacionComisionesRedeban

if 'informe_clientes_ventas' in PROYECTOS:
    from proyectos.informe_clientes_ventas.informe_clientes_ventas \
        import InformeClientesVentas

def main():
    nombre_proyecto = obtener_nombre_proyecto()
    # f = Figlet(font='slant')
    # print(f.renderText(nombre_proyecto))
    print(f"\nIniciando {nombre_proyecto}")
    obtener_parametros_insumos()
    

if __name__ == "__main__":
    main()




