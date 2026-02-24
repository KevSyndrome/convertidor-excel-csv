# src/utils/formato_bancario.py
import pandas as pd
from .limpieza import limpiar_celda

def formatear_nombre(texto, max_length=30):
    """Formatea el nombre aplicando limpieza y cortando a max_length caracteres"""
    if pd.isna(texto):
        return ''
    texto = limpiar_celda(texto)
    return texto[:max_length]

def formatear_importe(valor):
    """Formatea el importe como número con 2 decimales (sin .0)"""
    if pd.isna(valor):
        return '0.00'
    try:
        if isinstance(valor, str):
            valor = valor.replace(',', '').replace('$', '').strip()
        numero = float(valor)
        return f"{numero:.2f}"
    except:
        return '0.00'

def formatear_cuenta(cuenta, max_length=30):
    """Formatea la cuenta bancaria como string sin decimales"""
    if pd.isna(cuenta):
        return ''
    if isinstance(cuenta, (int, float)):
        cuenta = str(int(cuenta))
    else:
        cuenta = limpiar_celda(str(cuenta))
    return cuenta[:max_length]

def generar_csv_bancario(df, mapeo, inputs_adicionales, filas_eliminar):
    """
    Genera DataFrame con formato bancario de 8 columnas
    
    Columnas de salida:
    1. MXPRLF (cuenta bancaria)
    2. F (importe neto)
    3. Texto fijo (input usuario)
    4. Nombre (formateado y limpio)
    5. Vacío (en datos)
    6. Vacío (en datos)
    7. Vacío (en datos)
    8. Vacío (en datos)
    """
    
    # Filtrar filas a eliminar si es necesario
    if filas_eliminar:
        df = df.drop(filas_eliminar)
        df = df.reset_index(drop=True)
    
    # Obtener las columnas mapeadas
    nombre_col = mapeo.get('campo_nombre')
    importe_col = mapeo.get('campo_importe_neto')
    cuenta_col = mapeo.get('campo_cuenta')
    
    # Validar que existen las columnas
    if not all([nombre_col in df.columns, importe_col in df.columns, cuenta_col in df.columns]):
        raise ValueError("No se encontraron las columnas mapeadas en el archivo")
    
    # Preparar datos con limpieza
    nombres = df[nombre_col].apply(lambda x: formatear_nombre(x, 30))
    importes = df[importe_col].apply(formatear_importe)
    cuentas = df[cuenta_col].apply(formatear_cuenta)
    
    # Calcular suma total de importes
    suma_total = 0.0
    for imp in importes:
        try:
            if imp and imp != '':
                suma_total += float(imp)
        except:
            pass
    
    # Formatear suma total con 2 decimales
    suma_total_formateada = f"{suma_total:.2f}"
    
    # Obtener inputs adicionales y limpiarlos
    texto_col3 = limpiar_celda(inputs_adicionales.get('columna3_texto', ''))[:30]
    header_col3 = limpiar_celda(inputs_adicionales.get('columna3_header', ''))[:30]
    fecha_col6 = inputs_adicionales.get('columna6_fecha', '')
    texto_col8 = limpiar_celda(inputs_adicionales.get('columna8_texto', ''))[:30]
    
    # Calcular total de filas (excluyendo header)
    total_filas = len(df)
    
    # Crear lista de filas para el CSV
    filas_csv = []
    
    # HEADER - Fila 0
    filas_csv.append([
        'MXPRLF',                    # Col1: Header fijo
        'F',                         # Col2: Header fijo
        header_col3,                 # Col3: Header del input
        suma_total_formateada,        # Col4: SUMA TOTAL de importes netos
        str(total_filas),             # Col5: TOTAL DE FILAS
        fecha_col6,                   # Col6: Fecha
        '',                           # Col7: Vacío
        texto_col8                    # Col8: Header del input
    ])
    
    # DATOS - Filas siguientes
    for i in range(len(df)):
        filas_csv.append([
            cuentas.iloc[i],      # Col1: Cuenta bancaria
            importes.iloc[i],     # Col2: Importe neto
            texto_col3,           # Col3: Texto fijo (igual para todas)
            nombres.iloc[i],      # Col4: NOMBRE (CORREGIDO: antes estaba vacío)
            '',                   # Col5: Vacío en datos
            '',                   # Col6: Vacío en datos
            '',                   # Col7: Vacío en datos
            ''                    # Col8: Vacío en datos
        ])
    
    # Crear DataFrame sin índices
    df_final = pd.DataFrame(filas_csv)
    
    return df_final, suma_total_formateada