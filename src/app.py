from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
import os
from datetime import datetime

from utils import (
    # Limpieza
    limpiar_dataframe,
    convertir_valor_json,
    
    # Excel Handler
    detectar_fila_encabezado,
    limpiar_columnas_dataframe,
    procesar_excel,
    obtener_vista_previa,
    filtrar_dataframe,
    
    # File Manager
    generar_nombre_unico,
    generar_nombre_csv,
    guardar_archivo,
    guardar_dataframe_como_csv,
    limpiar_archivos_temporales,
    asegurar_directorios
)

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui_cambiala_por_una_segura'
app.config['SESSION_TYPE'] = 'filesystem'

APP_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(APP_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(APP_DIR, 'outputs')

asegurar_directorios([UPLOAD_FOLDER, OUTPUT_FOLDER])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER


@app.route('/')
def index():
    """Página principal"""
    session.pop('archivo_actual', None)
    session.pop('nombre_original', None)
    session.pop('temp_df', None)
    return render_template('index.html')


@app.route('/vista_previa', methods=['POST'])
def vista_previa():
    """Endpoint para obtener vista previa del Excel"""
    try:
        if 'archivo' not in request.files:
            return {'success': False, 'error': 'No se recibió archivo'}
        
        archivo = request.files['archivo']
        
        if archivo.filename == '':
            return {'success': False, 'error': 'No se seleccionó archivo'}
        
        if not archivo.filename.endswith(('.xlsx', '.xls')):
            return {'success': False, 'error': 'El archivo debe ser Excel'}
        
        filepath, nombre_unico = guardar_archivo(archivo, app.config['UPLOAD_FOLDER'])
        
        session['archivo_actual'] = nombre_unico
        session['nombre_original'] = archivo.filename
        
        df, fila_encabezado, total_filas = procesar_excel(filepath)
        
        temp_file = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_{nombre_unico}.pkl')
        df.to_pickle(temp_file)
        session['temp_df'] = f'temp_{nombre_unico}.pkl'
        
        datos_preview = obtener_vista_previa(df)
        
        return {
            'success': True,
            'columnas': df.columns.tolist(),
            'datos': datos_preview,
            'total_filas': total_filas,
            'filas_preview': len(datos_preview),
            'fila_encabezado': fila_encabezado,
            'mensaje': f'Archivo cargado correctamente: {archivo.filename}'
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


@app.route('/convertir', methods=['POST'])
def convertir():
    """Endpoint para convertir Excel a CSV"""
    try:
        if 'archivo_actual' not in session:
            flash('No hay ningún archivo cargado. Por favor, sube un archivo primero.', 'error')
            return redirect(url_for('index'))
        
        nombre_archivo = session['archivo_actual']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
        
        if not os.path.exists(filepath):
            flash('El archivo ya no existe. Por favor, súbelo de nuevo.', 'error')
            session.pop('archivo_actual', None)
            return redirect(url_for('index'))
        
        df, _, _ = procesar_excel(filepath)
        
        columnas_seleccionadas = request.form.getlist('columnas')
        filas_eliminar = request.form.getlist('filas_eliminar')
        
        df_filtrado = filtrar_dataframe(df, columnas_seleccionadas, filas_eliminar)
        
        if df_filtrado is None:
            flash('No se encontraron columnas válidas', 'error')
            return redirect(url_for('index'))
        
        df_filtrado = limpiar_dataframe(df_filtrado)
        
        nombre_csv, output_path = guardar_dataframe_como_csv(
            df_filtrado, 
            app.config['OUTPUT_FOLDER']
        )
        
        temp_file = os.path.join(app.config['UPLOAD_FOLDER'], session.get('temp_df', ''))
        limpiar_archivos_temporales(filepath, temp_file)
        
        session.pop('archivo_actual', None)
        session.pop('temp_df', None)
        session.pop('nombre_original', None)
        
        filas_eliminadas_count = len(filas_eliminar) if filas_eliminar else 0
        flash(f'Archivo convertido exitosamente: {len(df_filtrado)} filas | {len(df_filtrado.columns)} columnas | {filas_eliminadas_count} filas eliminadas', 'success')
        
        return render_template('index.html', 
                             csv_download=nombre_csv,
                             nombre_original=session.get('nombre_original', 'archivo'))
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error inesperado: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/descargar/<filename>')
def descargar(filename):
    """Endpoint para descargar archivo CSV"""
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        flash('El archivo ya no está disponible', 'error')
        return redirect(url_for('index'))
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename
    )


@app.route('/nueva_conversion')
def nueva_conversion():
    """Endpoint para iniciar una nueva conversión"""
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)