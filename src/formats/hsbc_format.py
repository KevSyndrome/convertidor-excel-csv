import pandas as pd
from ..core.data_cleaner import limpiar_celda
from .base_format import FormatoBancarioBase

class FormatoHSBC(FormatoBancarioBase):
    """
    Formato específico para HSBC - 8 columnas:
    1. MXPRLF (cuenta bancaria)
    2. F (importe neto)
    3. Texto fijo (input usuario)
    4. Nombre (formateado y limpio)
    5-8. Vacíos
    """
    
    def generar_csv(self, df):
        df = self._filtrar_filas(df)
        self._validar_columnas(df)
        
        nombre_col = self.mapeo.get('campo_nombre')
        importe_col = self.mapeo.get('campo_importe_neto')
        cuenta_col = self.mapeo.get('campo_cuenta')
        
        nombres = df[nombre_col].apply(lambda x: self._formatear_nombre(x))
        importes = df[importe_col].apply(self._formatear_importe)
        cuentas = df[cuenta_col].apply(self._formatear_cuenta)
        
        suma_total = self._calcular_suma_total(importes)
        
        texto_col3 = limpiar_celda(self.inputs_adicionales.get('columna3_texto', ''))[:30]
        header_col3 = limpiar_celda(self.inputs_adicionales.get('columna3_header', ''))[:30]
        fecha_col6 = self.inputs_adicionales.get('columna6_fecha', '')
        texto_col8 = limpiar_celda(self.inputs_adicionales.get('columna8_texto', ''))[:30]
        
        filas_csv = []
        
        # HEADER
        filas_csv.append([
            'MXPRLF',                    # Col1
            'F',                         # Col2
            header_col3,                 # Col3
            f"{suma_total:.2f}",         # Col4
            str(len(df)),                 # Col5
            fecha_col6,                   # Col6
            '',                           # Col7
            texto_col8                    # Col8
        ])
        
        # DATOS
        for i in range(len(df)):
            filas_csv.append([
                cuentas.iloc[i],
                f"{importes.iloc[i]:.2f}",
                texto_col3,
                nombres.iloc[i],
                '', '', '', ''
            ])
        
        return pd.DataFrame(filas_csv), f"{suma_total:.2f}"
    
    def _formatear_nombre(self, texto, max_length=30):
        if pd.isna(texto):
            return ''
        return limpiar_celda(texto)[:max_length]
    
    def _formatear_importe(self, valor):
        if pd.isna(valor):
            return 0.0
        try:
            if isinstance(valor, str):
                valor = valor.replace(',', '').replace('$', '').strip()
            return float(valor)
        except:
            return 0.0
    
    def _formatear_cuenta(self, cuenta, max_length=30):
        if pd.isna(cuenta):
            return ''
        if isinstance(cuenta, (int, float)):
            cuenta = str(int(cuenta))
        else:
            cuenta = limpiar_celda(str(cuenta))
        return cuenta[:max_length]
    
    def _calcular_suma_total(self, importes):
        return sum(importes)