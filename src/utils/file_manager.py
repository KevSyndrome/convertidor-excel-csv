# src/utils/file_manager.py
import os
import uuid
from datetime import datetime

def generar_nombre_unico(extension=''):
    """Genera un nombre único para archivos"""
    if extension and not extension.startswith('.'):
        extension = f'.{extension}'
    return f"{uuid.uuid4().hex}{extension}"

def generar_nombre_csv():
    """Genera un nombre para archivo CSV con timestamp"""
    return f"convertido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

def guardar_archivo(archivo, upload_folder):
    """
    Guarda un archivo subido y retorna la ruta y nombre único
    """
    extension = os.path.splitext(archivo.filename)[1]
    nombre_unico = generar_nombre_unico(extension)
    filepath = os.path.join(upload_folder, nombre_unico)
    archivo.save(filepath)
    return filepath, nombre_unico

def guardar_dataframe_como_csv(df, output_folder, nombre_archivo=None):
    """
    Guarda un DataFrame como CSV sin incluir índices
    """
    if nombre_archivo is None:
        nombre_archivo = generar_nombre_csv()
    
    output_path = os.path.join(output_folder, nombre_archivo)
    
    # Guardar CSV sin índice y sin header
    df.to_csv(output_path, index=False, header=False, encoding='utf-8')
    
    return nombre_archivo, output_path

def limpiar_archivos_temporales(*filepaths):
    """
    Elimina archivos temporales
    """
    for filepath in filepaths:
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

def asegurar_directorios(directorios):
    """
    Asegura que los directorios existan
    """
    for directorio in directorios:
        os.makedirs(directorio, exist_ok=True)