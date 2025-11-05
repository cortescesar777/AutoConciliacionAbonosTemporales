import logging
import os
from datetime import datetime
from functools import wraps

class Logger:
    _instance = None
    _last_log_date = None
    _file_handler = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize_logger(cls._instance)
        else:
            # Verificar si ha cambiado la fecha
            current_date = datetime.now().date()
            if cls._last_log_date != current_date:
                cls._instance._update_file_handler()
        return cls._instance
    
    def _initialize_logger(self):
        """Inicializa la configuración del logger"""
        self.logger = logging.getLogger('logger')
        self.logger.setLevel(logging.DEBUG)
        
        # Crear directorio logs si no existe
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Formato para los mensajes
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Inicializar el file handler
        self._update_file_handler()
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        console_handler.setLevel(logging.INFO)
        
        # Limpiar handlers existentes para evitar duplicados
        self.logger.handlers.clear()
        
        # Agregar handlers al logger
        self.logger.addHandler(self._file_handler)
        self.logger.addHandler(console_handler)
    
    def _update_file_handler(self):
        """Actualiza el file handler con un nuevo archivo de log"""
        # Actualizar la fecha del último log
        self.__class__._last_log_date = datetime.now().date()
        
        # Eliminar el file handler anterior si existe
        if self._file_handler and self._file_handler in self.logger.handlers:
            self.logger.removeHandler(self._file_handler)
            self._file_handler.close()
        
        # Crear nuevo file handler con timestamp actual
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._file_handler = logging.FileHandler(f'logs/{timestamp}_logger.log')
        self._file_handler.setFormatter(self.formatter)
        self._file_handler.setLevel(logging.DEBUG)
        
        # Si el logger ya está inicializado, agregar el nuevo handler
        if hasattr(self, 'logger'):
            self.logger.addHandler(self._file_handler)
    
    def info(self, message, module_name=None):
        """Registra un mensaje de nivel INFO"""
        if module_name:
            message = f"[{module_name}] {message}"
        self.logger.info(message)
    
    def error(self, message, module_name=None):
        """Registra un mensaje de nivel ERROR"""
        if module_name:
            message = f"[{module_name}] {message}"
        self.logger.error(message)
    
    def debug(self, message, module_name=None):
        """Registra un mensaje de nivel DEBUG"""
        if module_name:
            message = f"[{module_name}] {message}"
        self.logger.debug(message)
    
    def warning(self, message, module_name=None):
        """Registra un mensaje de nivel WARNING"""
        if module_name:
            message = f"[{module_name}] {message}"
        self.logger.warning(message)
    
    @staticmethod
    def log_execution(level='info'):
        """Decorador para registrar la ejecución de métodos"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                logger = Logger()
                module_name = func.__module__
                func_name = func.__name__
                
                logger_method = getattr(logger, level)
                logger_method(f"Iniciando ejecución de {func_name}", module_name)
                
                try:
                    result = func(*args, **kwargs)
                    logger_method(f"Finalizó ejecución de {func_name}", module_name)
                    return result
                except Exception as e:
                    logger.error(f"Error en {func_name}: {str(e)}", module_name)
                    raise
            return wrapper
        return decorator