from abc import ABC, abstractmethod
import pandas as pd

class FormatoBancarioBase(ABC):
    """Clase base para todos los formatos bancarios"""
    
    def __init__(self, mapeo, inputs_adicionales, filas_eliminar):
        self.mapeo = mapeo
        self.inputs_adicionales = inputs_adicionales
        self.filas_eliminar = filas_eliminar
    
    @abstractmethod
    def generar_csv(self, df):
        """Método principal que debe implementar cada formato"""
        pass
    
    def _filtrar_filas(self, df):
        """Filtra las filas a eliminar si es necesario"""
        if self.filas_eliminar:
            df = df.drop(self.filas_eliminar)
            df = df.reset_index(drop=True)
        return df
    
    def _validar_columnas(self, df):
        """Valida que existan las columnas mapeadas"""
        columnas_requeridas = [
            self.mapeo.get('campo_nombre'),
            self.mapeo.get('campo_importe_neto'),
            self.mapeo.get('campo_cuenta')
        ]
        for col in columnas_requeridas:
            if col not in df.columns:
                raise ValueError(f"Columna requerida no encontrada: {col}")
        return True