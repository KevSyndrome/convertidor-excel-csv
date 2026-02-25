import re
import unicodedata
import pandas as pd
import math

def eliminar_acentos(texto):
    """Elimina acentos de un texto"""
    if not isinstance(texto, str):
        return texto
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sin_acentos = ''.join(char for char in texto_normalizado 
                                 if unicodedata.category(char) != 'Mn')
    return texto_sin_acentos

def reemplazar_caracteres_especiales(texto):
    """Reemplaza caracteres especiales por sus equivalentes"""
    if not isinstance(texto, str):
        return texto
    replacements = {
        'ñ': 'n', 'Ñ': 'N', 'ü': 'u', 'Ü': 'U',
        'ö': 'o', 'Ö': 'O', 'ä': 'a', 'Ä': 'A',
        'ë': 'e', 'Ë': 'E', 'ï': 'i', 'Ï': 'I',
        '¡': '', '¿': '', '°': '', 'º': '', 'ª': '',
    }
    resultado = texto
    for char, replacement in replacements.items():
        resultado = resultado.replace(char, replacement)
    return resultado

def limpiar_espacios(texto):
    """Limpia espacios extras en un texto"""
    if not isinstance(texto, str):
        return texto
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def limpiar_celda(texto):
    """Limpia una celda aplicando todas las transformaciones"""
    if pd.isna(texto):
        return ''
    texto = str(texto)
    texto = eliminar_acentos(texto)
    texto = reemplazar_caracteres_especiales(texto)
    texto = limpiar_espacios(texto)
    return texto

def limpiar_dataframe(df):
    """Aplica limpieza a todas las celdas de un DataFrame"""
    df_limpio = df.copy()
    for columna in df_limpio.columns:
        df_limpio[columna] = df_limpio[columna].apply(limpiar_celda)
    return df_limpio

def convertir_valor_json(valor):
    """Convierte valores a tipos válidos para JSON"""
    if pd.isna(valor):
        return ''
    if isinstance(valor, (int, float)):
        if math.isnan(valor) or math.isinf(valor):
            return ''
        return valor
    return str(valor)

def limpiar_nombre_columna(columna):
    """Limpia un nombre de columna"""
    col_str = str(columna).strip()
    if col_str.startswith('Unnamed') or col_str == '' or col_str == 'nan':
        return None
    return limpiar_celda(col_str)