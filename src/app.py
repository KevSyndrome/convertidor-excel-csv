from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
import os
import pandas as pd

from utils import (
    procesar_excel,
    obtener_vista_previa,
    guardar_archivo,
    guardar_dataframe_como_csv,
    limpiar_archivos_temporales,
    generar_csv_bancario
)

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui_cambiala_por_una_segura'

APP_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(APP_DIR, 'outputs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER


@app.route('/')
def index():
    session.clear()
    return render_template('index.html')


@app.route('/vista_previa', methods=['POST'])
def vista_previa():
    try:
        if 'archivo' not in request.files:
            return {'success': False, 'error': 'No se recibió archivo'}
        
        archivo = request.files['archivo']
        
        if archivo.filename == '':
            return {'success': False, 'error': 'No se seleccionó archivo'}
        
        if not archivo.filename.endswith(('.xlsx', '.xls')):
            return {'success': False, 'error': 'El archivo debe ser Excel'}
        
        filepath, nombre_unico = guardar_archivo(archivo, UPLOAD_FOLDER)
        session['archivo_actual'] = nombre_unico
        session['nombre_original'] = archivo.filename
        
        df, _, total_filas = procesar_excel(filepath)
        datos_preview = obtener_vista_previa(df)
        
        return {
            'success': True,
            'columnas': df.columns.tolist(),
            'datos': datos_preview,
            'total_filas': total_filas,
            'filas_preview': len(datos_preview)
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


@app.route('/convertir', methods=['POST'])
def convertir():
    try:
        if 'archivo_actual' not in session:
            flash('Sube un archivo primero', 'error')
            return redirect(url_for('index'))
        
        filepath = os.path.join(UPLOAD_FOLDER, session['archivo_actual'])
        
        if not os.path.exists(filepath):
            flash('El archivo ya no existe', 'error')
            session.clear()
            return redirect(url_for('index'))
        
        # Obtener datos del formulario
        mapeo = {
            'campo_nombre': request.form.get('nombre_columna'),
            'campo_importe_neto': request.form.get('importe_columna'),
            'campo_cuenta': request.form.get('cuenta_columna')
        }
        
        adicionales = {
            'columna3_texto': request.form.get('col3_texto', ''),
            'columna3_header': request.form.get('col3_header', ''),
            'columna6_fecha': request.form.get('col6_fecha', ''),
            'columna8_texto': request.form.get('col8_texto', '')
        }
        
        filas_eliminar_str = request.form.get('filas_eliminadas', '')
        filas_eliminar = [int(x) for x in filas_eliminar_str.split(',') if x.strip().isdigit()]
        
        # Validaciones
        if not all(mapeo.values()):
            flash('Selecciona las columnas requeridas (Nombre, Importe y Cuenta)', 'error')
            return redirect(url_for('index'))
        
        if not all(adicionales.values()):
            flash('Completa todos los campos adicionales', 'error')
            return redirect(url_for('index'))
        
        if len(adicionales['columna6_fecha']) != 8 or not adicionales['columna6_fecha'].isdigit():
            flash('La fecha debe tener 8 dígitos (DDMMYYYY)', 'error')
            return redirect(url_for('index'))
        
        # Cargar DataFrame
        df, _, _ = procesar_excel(filepath)
        
        # Generar CSV con formato bancario
        df_final, total = generar_csv_bancario(df, mapeo, adicionales, filas_eliminar)
        
        # Guardar como CSV
        nombre_csv, output_path = guardar_dataframe_como_csv(df_final, OUTPUT_FOLDER)
        
        # Limpiar temporales
        limpiar_archivos_temporales(filepath)
        session.clear()
        
        flash(f'✅ {len(df_final)-1} registros | Total: ${total}', 'success')
        return render_template('index.html', csv_download=nombre_csv)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/descargar/<filename>')
def descargar(filename):
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(filepath):
        flash('Archivo no disponible', 'error')
        return redirect(url_for('index'))
    return send_file(filepath, as_attachment=True, download_name=filename)


# CORREGIDO: Cambiado de '/nueva' a '/nueva_conversion' para que coincida con el HTML
@app.route('/nueva_conversion')
def nueva_conversion():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)