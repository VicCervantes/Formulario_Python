from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def init_db():
    with sqlite3.connect('mydatabase.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            department TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            creator_name TEXT NOT NULL,
            question TEXT,
            type TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER,
            form_id INTEGER,
            question_id INTEGER,
            answer TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(form_id) REFERENCES forms(id),
            FOREIGN KEY(question_id) REFERENCES forms(id)
        )
        ''')
init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')
        nombre = request.form.get('name')

        if usuario and contraseña and nombre:
            with sqlite3.connect('mydatabase.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (usuario, contraseña))
                user = cursor.fetchone()
                if user:
                    session['user_id'] = user[0]
                    session['name'] = nombre  
                    return redirect(url_for('opciones'))
                else:
                    flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/opciones', methods=['POST', 'GET'])
def opciones():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        departamento = request.form.get('departamento')

        if departamento:
            with sqlite3.connect('mydatabase.db') as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET department = ? WHERE id = ?', (departamento, user_id))
                conn.commit()
                flash('Departamento actualizado correctamente.', 'success')
                return redirect(url_for('opciones'))

    return render_template('opciones.html')

@app.route('/crear', methods=['GET', 'POST'])
def crear():
    if request.method == 'POST':
        user_id = session.get('user_id')
        creator_name = session.get('name')
        if user_id and creator_name:
            nuevas_preguntas = request.form.getlist('pregunta')
            tipos = request.form.getlist('tipo')
            with sqlite3.connect('mydatabase.db') as conn:
                cursor = conn.cursor()
                for pregunta, tipo in zip(nuevas_preguntas, tipos):
                    cursor.execute('INSERT INTO forms (user_id, creator_name, question, type) VALUES (?, ?, ?, ?)', 
                                   (user_id, creator_name, pregunta, tipo))
                conn.commit()
        flash('Formulario creado correctamente.', 'success')
        return redirect(url_for('crear'))
    return render_template('crear.html')


@app.route('/responder', methods=['GET', 'POST'])
def responder():
    user_id = session.get('user_id')
    name = session.get('name')
    if not user_id:
        return redirect(url_for('login'))

    if request.method == 'POST':
        with sqlite3.connect('mydatabase.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM forms WHERE user_id = ?', (user_id,))
            forms = cursor.fetchall()
            for form in forms:
                form_id = form[0]
                question_id = form_id  
                respuesta = request.form.get(f'respuesta_{form_id}')
                if respuesta: 
                    cursor.execute('INSERT INTO answers (name, user_id, form_id, question_id, answer) VALUES (?, ?, ?, ?, ?)', 
                                   (name, user_id, form_id, question_id, respuesta))
            conn.commit()
        flash('Respuestas enviadas. correctamente.', 'success')
        return redirect(url_for('opciones'))

    with sqlite3.connect('mydatabase.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, question, type FROM forms WHERE user_id = ?', (user_id,))
        questions = cursor.fetchall()
    return render_template('responder.html', questions=questions)

@app.route('/visualizar_respuestas')
def visualizar_respuestas():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    with sqlite3.connect('mydatabase.db') as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT name
            FROM answers
            WHERE user_id = ?
        ''', (user_id,))
        nombres = cursor.fetchall()

        respuestas_por_nombre = {}
        for nombre in nombres:
            cursor.execute('''
                SELECT f.question, a.answer
                FROM answers a
                JOIN forms f ON a.question_id = f.id
                WHERE a.user_id = ? AND a.name = ?
            ''', (user_id, nombre[0]))
            respuestas_por_nombre[nombre[0]] = cursor.fetchall()
    
    return render_template('visualizar_respuestas.html', respuestas_por_nombre=respuestas_por_nombre)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']
        with sqlite3.connect('mydatabase.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (usuario, contraseña))
            conn.commit()
        flash('Usuario creado correctamente.', 'success')
        return redirect(url_for('crear_usuario'))
    return render_template('crear_usuario.html')

if __name__ == '__main__':
    app.run(debug=True)