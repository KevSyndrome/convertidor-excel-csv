from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
import pandas as pd
import os
import re
import unicodedata
import math
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui_cambiala_por_una_segura'
app.config['SESSION_TYPE'] = 'filesystem'

# ==================== RUTAS ====================
APP_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(APP_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(APP_DIR, 'outputs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
# ==============================================


# ==================== FUNCIONES DE LIMPIEZA ====================
def eliminar_acentos(texto):
    if not isinstance(texto, str):
        return texto
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sin_acentos = ''.join(char for char in texto_normalizado 
                                 if unicodedata.category(char) != 'Mn')
    return texto_sin_acentos


def reemplazar_caracteres_especiales(texto):
    if not isinstance(texto, str):
        return texto
    replacements = {
        'ñ': 'n', 'Ñ': 'N',
        'ü': 'u', 'Ü': 'U',
        'ö': 'o', 'Ö': 'O',
        'ä': 'a', 'Ä': 'A',
        'ë': 'e', 'Ë': 'E',
        'ï': 'i', 'Ï': 'I',
        '¡': '', '¿': '',
        '°': '', 'º': '', 'ª': '',
    }
    resultado = texto
    for char, replacement in replacements.items():
        resultado = resultado.replace(char, replacement)
    return resultado


def limpiar_espacios(texto):
    if not isinstance(texto, str):
        return texto
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def limpiar_celda(texto):
    if pd.isna(texto):
        return ''
    texto = str(texto)
    texto = eliminar_acentos(texto)
    texto = reemplazar_caracteres_especiales(texto)
    texto = limpiar_espacios(texto)
    return texto


def limpiar_dataframe(df):
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


def detectar_fila_encabezado(df, max_filas=20):
    """Detecta automáticamente en qué fila están los encabezados reales"""
    for i in range(min(max_filas, len(df))):
        fila = df.iloc[i]
        no_nulos = fila.notna().sum()
        if no_nulos > len(fila) / 2:
            return i
    return 0
# ============================================================


@app.route('/')
def index():
    # Limpiar la sesión al cargar la página principal
    session.pop('archivo_actual', None)
    session.pop('nombre_archivo', None)
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
        
        # Generar nombre único para evitar conflictos
        extension = os.path.splitext(archivo.filename)[1]
        nombre_unico = f"{uuid.uuid4().hex}{extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], nombre_unico)
        archivo.save(filepath)
        
        # Guardar referencia en sesión
        session['archivo_actual'] = nombre_unico
        session['nombre_original'] = archivo.filename
        
        # Leer Excel
        df_raw = pd.read_excel(filepath, header=None)
        
        # Detectar fila de encabezados
        fila_encabezado = detectar_fila_encabezado(df_raw)
        
        # Leer Excel con el encabezado correcto
        df = pd.read_excel(filepath, header=fila_encabezado)
        
        # Limpiar nombres de columnas
        columnas_limpias = []
        for col in df.columns:
            col_str = str(col).strip()
            if col_str.startswith('Unnamed') or col_str == '' or col_str == 'nan':
                columnas_limpias.append(f'Columna_{len(columnas_limpias)+1}')
            else:
                columnas_limpias.append(limpiar_celda(col_str))
        
        df.columns = columnas_limpias
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        df = df.reset_index(drop=True)
        
        # Guardar DataFrame completo temporalmente
        temp_file = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_{nombre_unico}.pkl')
        df.to_pickle(temp_file)
        session['temp_df'] = f'temp_{nombre_unico}.pkl'
        
        # Obtener primeros 100 registros para vista previa
        df_preview = df.head(100)
        
        # Convertir a diccionario
        datos = []
        for idx, fila in df_preview.iterrows():
            fila_dict = {'__indice_real__': idx}
            for col in df.columns:
                fila_dict[col] = convertir_valor_json(fila[col])
            datos.append(fila_dict)
        
        return {
            'success': True,
            'columnas': df.columns.tolist(),
            'datos': datos,
            'total_filas': len(df),
            'filas_preview': len(datos),
            'fila_encabezado': fila_encabezado,
            'mensaje': f'Archivo cargado correctamente: {archivo.filename}'
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


@app.route('/convertir', methods=['POST'])
def convertir():
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
        
        try:
            # Leer Excel
            df_raw = pd.read_excel(filepath, header=None)
            fila_encabezado = detectar_fila_encabezado(df_raw)
            df = pd.read_excel(filepath, header=fila_encabezado)
            
            # Limpiar columnas
            columnas_limpias = []
            for col in df.columns:
                col_str = str(col).strip()
                if col_str.startswith('Unnamed') or col_str == '' or col_str == 'nan':
                    columnas_limpias.append(f'Columna_{len(columnas_limpias)+1}')
                else:
                    columnas_limpias.append(limpiar_celda(col_str))
            
            df.columns = columnas_limpias
            df = df.dropna(how='all')
            df = df.reset_index(drop=True)
            
        except Exception as e:
            flash(f'Error al leer el Excel: {str(e)}', 'error')
            return redirect(url_for('index'))
        
        # Obtener datos del formulario
        columnas_seleccionadas = request.form.getlist('columnas')
        filas_eliminar = request.form.getlist('filas_eliminar')
        
        if not columnas_seleccionadas:
            columnas_seleccionadas = df.columns.tolist()
        
        columnas_validas = [col for col in columnas_seleccionadas if col in df.columns]
        
        if not columnas_validas:
            flash('No se encontraron columnas válidas', 'error')
            return redirect(url_for('index'))
        
        # Crear copia para filtrar
        df_filtrado = df[columnas_validas].copy()
        
        # Eliminar filas por índice real
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
        
        # Aplicar limpieza
        df_filtrado = limpiar_dataframe(df_filtrado)
        
        # Generar nombre y guardar
        nombre_csv = f"convertido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], nombre_csv)
        
        df_filtrado.to_csv(output_path, index=False, encoding='utf-8')
        
        # Limpiar archivos temporales
        if os.path.exists(filepath):
            os.remove(filepath)
        
        temp_file = os.path.join(app.config['UPLOAD_FOLDER'], session.get('temp_df', ''))
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        # Limpiar sesión
        session.pop('archivo_actual', None)
        session.pop('temp_df', None)
        
        filas_eliminadas_count = len(filas_eliminar) if filas_eliminar else 0
        flash(f'✅ Archivo convertido exitosamente: {len(df_filtrado)} filas | {len(columnas_validas)} columnas | {filas_eliminadas_count} filas eliminadas', 'success')
        
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
    # Limpiar sesión y redirigir para nueva conversión
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)