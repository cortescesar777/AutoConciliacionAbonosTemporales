import pandas

def reducir(series):
       
    idx = series.first_valid_index()
    if idx is None:
        return None
    return series.loc[idx]


def excel_a_csv(rutas):
    print(f"rutas: {rutas}")
    excel = pandas.ExcelFile(rutas[0])
    # print(f"{excel}")
    df = excel.parse(sheetname=0, index_col=None, na_values=['NA'])
    df.to_csv(rutas[1], index=None)

    return df


