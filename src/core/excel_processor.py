import pandas as pd
from .data_cleaner import limpiar_nombre_columna, convertir_valor_json

def detectar_fila_encabezado(df, max_filas=20):
    """Detecta automáticamente en qué fila están los encabezados reales"""
    for i in range(min(max_filas, len(df))):
        fila = df.iloc[i]
        no_nulos = fila.notna().sum()
        if no_nulos > len(fila) / 2:
            return i
    return 0

def limpiar_columnas_dataframe(df):
    """Limpia los nombres de las columnas del DataFrame"""
    columnas_limpias = []
    contador_columnas = 1
    
    for col in df.columns:
        col_limpia = limpiar_nombre_columna(col)
        if col_limpia is None:
            col_limpia = f'Columna_{contador_columnas}'
            contador_columnas += 1
        columnas_limpias.append(col_limpia)
    
    return columnas_limpias

def procesar_excel(filepath):
    """
    Procesa un archivo Excel y retorna el DataFrame limpio
    Returns: (DataFrame, fila_encabezado, total_filas)
    """
    df_raw = pd.read_excel(filepath, header=None)
    fila_encabezado = detectar_fila_encabezado(df_raw)
    df = pd.read_excel(filepath, header=fila_encabezado)
    columnas_limpias = limpiar_columnas_dataframe(df)
    df.columns = columnas_limpias
    df = df.dropna(how='all')
    df = df.reset_index(drop=True)
    return df, fila_encabezado, len(df)

def obtener_vista_previa(df, limite=100):
    """
    Obtiene una vista previa del DataFrame para JSON
    """
    df_preview = df.head(limite)
    datos = []
    for idx, fila in df_preview.iterrows():
        fila_dict = {'__indice_real__': idx}
        for col in df.columns:
            fila_dict[col] = convertir_valor_json(fila[col])
        datos.append(fila_dict)
    return datos