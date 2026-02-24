# src/utils/excel_handler.py
import pandas as pd
from .limpieza import limpiar_nombre_columna, convertir_valor_json

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
    # Leer Excel sin encabezado para detectar
    df_raw = pd.read_excel(filepath, header=None)
    
    # Detectar fila de encabezados
    fila_encabezado = detectar_fila_encabezado(df_raw)
    
    # Leer Excel con el encabezado correcto
    df = pd.read_excel(filepath, header=fila_encabezado)
    
    # Limpiar nombres de columnas
    columnas_limpias = limpiar_columnas_dataframe(df)
    df.columns = columnas_limpias
    
    # Eliminar filas completamente vacías
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


def filtrar_dataframe(df, columnas_seleccionadas, filas_eliminar):
    """
    Filtra un DataFrame según columnas seleccionadas y filas a eliminar
    """
    if not columnas_seleccionadas:
        columnas_seleccionadas = df.columns.tolist()
    
    columnas_validas = [col for col in columnas_seleccionadas if col in df.columns]
    
    if not columnas_validas:
        return None
    
    df_filtrado = df[columnas_validas].copy()
    
    if filas_eliminar:
        indices_eliminar = []
        for idx in filas_eliminar:
            try:
                indices_eliminar.append(int(idx))
            except:
                pass
        
        if indices_eliminar:
            indices_validos = [i for i in indices_eliminar if i < len(df_filtrado)]
            df_filtrado = df_filtrado.drop(indices_validos)
            df_filtrado = df_filtrado.reset_index(drop=True)
    
    return df_filtrado