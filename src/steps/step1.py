def seleccionar_archivo(titulo="Seleccionar archivo", tipos_archivo=None):
    try:
        import tkinter as tk
        from tkinter import filedialog

        # Ocultar la ventana principal de Tkinter
        root = tk.Tk()
        root.withdraw()

        # Configurar tipos de archivo por defecto si no se especifican
        if tipos_archivo is None:
            tipos_archivo = [
                ('Archivos Excel', '*.xlsx *.xls')
            ]

        # Mostrar el diálogo de selección de archivo
        ruta_archivo = filedialog.askopenfilename(
            title=titulo,
            filetypes=tipos_archivo
        )

        return ruta_archivo if ruta_archivo else None

    except ImportError:
        print("Error: No se pudo importar tkinter. Asegúrate de tenerlo instalado.")
        return None
    except Exception as e:
        print(f"Error al seleccionar archivo: {str(e)}")
        return None
