from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
import os
import pandas as pd

from src.core import (
    procesar_excel,
    obtener_vista_previa
)
from src.core.file_manager import (
    guardar_archivo,
    guardar_dataframe_como_csv,
    limpiar_archivos_temporales
)
from src.factories import FormatFactory

app = Flask(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.template_folder = os.path.join(PROJECT_ROOT, 'templates')

app.secret_key = os.environ.get('SECRET_KEY', 'clave-flask-app')

APP_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(APP_DIR, 'uploads'))
OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', os.path.join(APP_DIR, 'outputs'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def limpiar_carpetas():
    """Elimina todos los archivos de las carpetas uploads y outputs"""
    for carpeta in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        if os.path.exists(carpeta):
            for archivo in os.listdir(carpeta):
                ruta_archivo = os.path.join(carpeta, archivo)
                try:
                    if os.path.isfile(ruta_archivo):
                        os.remove(ruta_archivo)
                except Exception as e:
                    print(f"Error al eliminar {ruta_archivo}: {e}")

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
        
        # ============================================
        # OBTENER BANCO SELECCIONADO (por defecto HSBC)
        # ============================================
        banco = request.form.get('banco', 'hsbc')  # 'hsbc' es el valor por defecto
        
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
        
        if not all(mapeo.values()):
            flash('Selecciona las columnas requeridas (Nombre, Importe y Cuenta)', 'error')
            return redirect(url_for('index'))
        
        if not all(adicionales.values()):
            flash('Completa todos los campos adicionales', 'error')
            return redirect(url_for('index'))
        
        if len(adicionales['columna6_fecha']) != 8 or not adicionales['columna6_fecha'].isdigit():
            flash('La fecha debe tener 8 dígitos (DDMMYYYY)', 'error')
            return redirect(url_for('index'))
        
        # ============================================
        # PROCESAR ARCHIVO Y GENERAR CSV USANDO LA FÁBRICA
        # ============================================
        df, _, _ = procesar_excel(filepath)
        
        formato = FormatFactory.crear_formato(
            banco=banco,
            mapeo=mapeo,
            inputs_adicionales=adicionales,
            filas_eliminar=filas_eliminar
        )
        
        df_final, total = formato.generar_csv(df)
        
        nombre_csv, output_path = guardar_dataframe_como_csv(df_final, OUTPUT_FOLDER)
        
        # Limpiar archivo temporal
        limpiar_archivos_temporales(filepath)
        session.clear()
        
        nombre_banco = {
            'hsbc': 'HSBC',
            'banorte': 'Banorte',
            'bbva': 'BBVA',
            'santander': 'Santander'
        }.get(banco, banco.upper())
        
        flash(f'{len(df_final)-1} registros | Formato: {nombre_banco}', 'success')
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
        return redirect(url_for('nueva_conversion'))
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/nueva_conversion')
def nueva_conversion():
    limpiar_carpetas()
    session.clear()
    return redirect(url_for('index'))

@app.before_request
def verificar_sesion():
    """Verifica que el archivo en sesión aún exista"""
    if 'archivo_actual' in session:
        filepath = os.path.join(UPLOAD_FOLDER, session['archivo_actual'])
        if not os.path.exists(filepath):
            session.clear()
            flash('La sesión ha expirado o el archivo ya no existe', 'error')
            return redirect(url_for('nueva_conversion'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)