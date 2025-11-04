import pandas as pd

class ExcelComparator:
    def __init__(self, df1, df2, key_column, columns_to_compare=None):
        """ Inicializa el comparador de Excel. Args: df1 (DataFrame): Primer DataFrame a comparar df2 (DataFrame): Segundo DataFrame a comparar key_column (str): Columna que sirve como clave para comparar registros columns_to_compare (list): Lista de columnas a comparar (si es None, compara todas) """
        self.df1 = df1
        self.df2 = df2
        self.key_column = key_column
        self.columns_to_compare = columns_to_compare if columns_to_compare else df1.columns.tolist()
        
        # Asegurarse de que la columna clave esté en la lista de columnas a comparar
        if key_column not in self.columns_to_compare:
            self.columns_to_compare.append(key_column)
    
    def compare(self):
        """ Compara los dos DataFrames. Returns: dict: Resultados de la comparación """
        # Verificar si las columnas existen en ambos DataFrames
        for col in self.columns_to_compare:
            if col not in self.df1.columns or col not in self.df2.columns:
                raise ValueError(f"La columna '{col}' no existe en ambos DataFrames")
        
        # Filtrar DataFrames para incluir solo las columnas a comparar
        df1_filtered = self.df1[self.columns_to_compare].copy()
        df2_filtered = self.df2[self.columns_to_compare].copy()
        
        # Convertir la columna clave a string para evitar problemas de tipo
        df1_filtered[self.key_column] = df1_filtered[self.key_column].astype(str)
        df2_filtered[self.key_column] = df2_filtered[self.key_column].astype(str)
        
        # Establecer la columna clave como índice
        df1_filtered.set_index(self.key_column, inplace=True)
        df2_filtered.set_index(self.key_column, inplace=True)
        
        # Encontrar claves únicas en cada DataFrame
        keys1 = set(df1_filtered.index)
        keys2 = set(df2_filtered.index)
        
        # Claves que están en df1 pero no en df2
        only_in_df1 = keys1 - keys2
        # Claves que están en df2 pero no en df1
        only_in_df2 = keys2 - keys1
        # Claves que están en ambos
        common_keys = keys1 & keys2
        
        # Comparar valores para las claves comunes
        differences = {}
        for key in common_keys:
            row1 = df1_filtered.loc[key]
            row2 = df2_filtered.loc[key]
            
            # Comparar valores columna por columna
            row_differences = {}
            for col in self.columns_to_compare:
                if col == self.key_column:
                    continue
                
                val1 = row1[col]
                val2 = row2[col]
                
                # Manejar valores NaN
                if pd.isna(val1) and pd.isna(val2):
                    continue
                elif pd.isna(val1) or pd.isna(val2) or val1 != val2:
                    row_differences[col] = {
                        'df1_value': str(val1) if not pd.isna(val1) else 'NaN',
                        'df2_value': str(val2) if not pd.isna(val2) else 'NaN'
                    }
            
            if row_differences:
                differences[key] = row_differences
        
        return {
            'only_in_df1': list(only_in_df1),
            'only_in_df2': list(only_in_df2),
            'differences': differences,
            'total_records_df1': len(df1_filtered),
            'total_records_df2': len(df2_filtered),
            'total_differences': len(differences)
        }
    
    def generate_difference_report(self):
        """ Genera un DataFrame con las diferencias encontradas. Returns: DataFrame: Reporte de diferencias """
        comparison_result = self.compare()
        differences = comparison_result['differences']
        
        if not differences:
            return pd.DataFrame(columns=[self.key_column, 'column', 'df1_value', 'df2_value'])
        
        records = []
        for key, diff_dict in differences.items():
            for col, values in diff_dict.items():
                records.append({
                    self.key_column: key,
                    'column': col,
                    'df1_value': values['df1_value'],
                    'df2_value': values['df2_value']
                })
        
        return pd.DataFrame(records)
