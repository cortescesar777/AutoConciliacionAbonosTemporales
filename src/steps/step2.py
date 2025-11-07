from src.core.reader import ExcelReader


def leer_archivo(path_archivo, app_state):
    app_state.set_dataframe("dataFrameOriginal", ExcelReader.read_excel_file(path_archivo))
