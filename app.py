import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = 'taller_tci_clave_absoluta_2026'

# Contraseña del panel de administración
ADMIN_PASSWORD = 'motita2024abc'

# Conexión definitiva a la base de datos Supabase
DATABASE_URL = os.environ.get(
    'DATABASE_URL', 
    'postgresql://postgres:motita2024abc@db.fzewcrztnmfskeukmosx.supabase.co:5432/postgres'
)

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Inicializar la base de datos y crear la tabla si no existe
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                categoria TEXT NOT NULL,
                precio REAL NOT NULL,
                imagen TEXT NOT NULL
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error al inicializar la BD:", e)

init_db()

# Ruta API para conectar con tu app.js si lo necesitas
@app.route('/api/products', methods=['GET'])
def get_products_api():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, nombre, categoria, precio, imagen FROM productos')
        rows = cur.fetchall()
        cur.close()
        conn.close()

        productos_lista = []
        for row in rows:
            prod_id, nombre, categoria, precio, imagen = row
            img_url = imagen if imagen.startswith('http') else url_for('static', filename='img/' + imagen, _external=True)
            
            productos_lista.append({
                'id': prod_id,
                'name': nombre,
                'category': categoria.lower(),
                'price': float(precio),
                'priceFormatted': f"S/. {float(precio):.2f}",
                'img': img_url,
                'desc': 'Producto oficial respaldado por Politécnico Pedro Abel Labarthe Durand.'
            })

        return jsonify({'status': 'success', 'data': productos_lista})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# --- RUTA PRINCIPAL (ENTRADA DIRECTA AL LOGIN) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    # Si el usuario intenta hacer login desde la página principal
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Contraseña incorrecta')

    # Si ya está logueado, lo mandamos al panel de administración directamente
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    
    # Si no hay sesión, muestra el login por defecto en http://127.0.0.1:5000/
    return render_template('login.html')

# --- PANEL DE ADMINISTRACIÓN (PROTEGIDO) ---
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, nombre, categoria, precio, imagen FROM productos')
    productos = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', productos=productos)

# Ruta de compatibilidad por si tu HTML usa /admin
@app.route('/admin')
def admin_redirect():
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/agregar', methods=['POST'])
def agregar_producto():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
        
    nombre = request.form.get('nombre')
    categoria = request.form.get('categoria')
    precio = request.form.get('precio')
    
    imagen = request.form.get('imagen_url', '')
    if 'imagen_archivo' in request.files:
        file = request.files['imagen_archivo']
        if file and file.filename != '':
            filename = file.filename
            file.save(os.path.join('static/img', filename))
            imagen = filename

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO productos (nombre, categoria, precio, imagen) VALUES (%s, %s, %s, %s)',
        (nombre, categoria, float(precio), imagen)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_producto(id):
    if not session.get('logged_in'):
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM productos WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)