import os
import sys
from config.properties import PropertiesReader
from core.reader import ExcelReader
from core.comparator import ExcelComparator

def main():
    # Obtener la ruta base del proyecto
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Cargar configuración
    config_path = os.path.join(base_path, 'config', 'config.properties')
    try:
        config = PropertiesReader(config_path)
    except Exception as e:
        print(f"Error al leer el archivo de configuración: {str(e)}")
        sys.exit(1)
    
    # Obtener rutas de archivos Excel
    file1_path = os.path.join(base_path, config.get_property('excel.file1.path'))
    file2_path = os.path.join(base_path, config.get_property('excel.file2.path'))
    
    # Obtener configuración de comparación
    columns_to_compare = config.get_list_property('comparison.columns')
    key_column = config.get_property('comparison.key_column')
    
    try:
        # Leer archivos Excel
        print(f"Leyendo archivo 1: {file1_path}")
        df1 = ExcelReader.read_excel_file(file1_path)
        
        # Aplicar filtro si está configurado
        filter_partidas = config.get_property('filter.partidas')
        filter_abonos = config.get_property('filter.partidas.abonos')
        filter_reversos = config.get_property('filter.partidas.reversos')
        
        if filter_partidas and filter_abonos and filter_reversos:
            print(f"\nAplicando filtro: {filter_partidas} in ({filter_abonos},{filter_reversos})")
            df1 = df1[df1[filter_partidas] == filter_abonos] or df1[df1[filter_partidas] == filter_reversos]
            print(f"Archivo 1 después del filtro: {len(df1)} registros")

        # print(f"Leyendo archivo 2: {file2_path}")
        # df2 = ExcelReader.read_excel_file(file2_path)

        ## Crear comparador
        # print("Comparando archivos...")
        # comparator = ExcelComparator(df1, df2, key_column, columns_to_compare)
        #
        # # Realizar comparación
        # comparison_result = comparator.compare()
        #
        # # Mostrar resultados
        # print("\nResultados de la comparación:")
        # print(f"Total registros en archivo 1: {comparison_result['total_records_df1']}")
        # print(f"Total registros en archivo 2: {comparison_result['total_records_df2']}")
        # print(f"Registros solo en archivo 1: {len(comparison_result['only_in_df1'])}")
        # print(f"Registros solo en archivo 2: {len(comparison_result['only_in_df2'])}")
        # print(f"Registros con diferencias: {comparison_result['total_differences']}")
        #
        # # Generar reporte de diferencias
        # differences_df = comparator.generate_difference_report()
        # if not differences_df.empty:
        #     print("\nDetalle de diferencias:")
        #     print(differences_df)
        #
        #     # Guardar reporte en Excel
        #     report_path = os.path.join(base_path, 'comparison_report.xlsx')
        #     differences_df.to_excel(report_path, index=False)
        #     print(f"\nReporte guardado en: {report_path}")
        # else:
        #     print("\nNo se encontraron diferencias entre los archivos.")
        
    except Exception as e:
        print(f"Error durante la comparación: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
