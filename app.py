from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
import sqlite3, json, os

app = Flask(__name__)
app.secret_key = 'top_secret_flag_machine'
DB = 'db.sqlite3'

# Чтение задач
with open('tasks.json', encoding='utf-8') as f:
    TASKS = json.load(f)

# Инициализация БД
def init_db():
    with sqlite3.connect(DB) as con:
        c = con.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                score INTEGER DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS solves (
                id INTEGER PRIMARY KEY,
                team_id INTEGER,
                challenge TEXT,
                FOREIGN KEY(team_id) REFERENCES teams(id)
            )
        ''')
        con.commit()

# Главная страница
@app.route('/')
def home():
    return render_template('home.html')

# Страница с тасками
@app.route('/tasks')
def tasks():
    if 'team' not in session:
        return redirect('/login')
    return render_template('tasks.html', tasks=TASKS)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        with sqlite3.connect(DB) as con:
            try:
                con.execute('INSERT INTO teams (name, password) VALUES (?, ?)', (name, password))
                return redirect('/login')
            except sqlite3.IntegrityError:
                return render_template('register.html', error="Команда уже существует")
    return render_template('register.html')

# Логин
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        with sqlite3.connect(DB) as con:
            result = con.execute('SELECT id FROM teams WHERE name=? AND password=?', (name, password)).fetchone()
            if result:
                session['team'] = result[0]
                return redirect('/')
        return render_template('login.html', error="Неверные данные")
    return render_template('login.html')

# Просмотр и отправка флага
@app.route('/challenge/<id>', methods=['GET', 'POST'])
def challenge(id):
    if 'team' not in session:
        return redirect('/login')
    ch = TASKS.get(id)
    if not ch:
        return "Задача не найдена", 404
    solved = False
    with sqlite3.connect(DB) as con:
        c = con.cursor()
        c.execute('SELECT 1 FROM solves WHERE team_id=? AND challenge=?', (session['team'], id))
        solved = c.fetchone()
        if request.method == 'POST' and not solved:
            submitted_flag = request.form['flag'].strip()
            if submitted_flag == ch['flag']:
                c.execute('INSERT INTO solves (team_id, challenge) VALUES (?, ?)', (session['team'], id))
                c.execute('UPDATE teams SET score = score + ? WHERE id = ?', (ch['value'], session['team']))
                con.commit()
                return render_template('challenge.html', ch=ch, correct=True)
            else:
                return render_template('challenge.html', ch=ch, incorrect=True)
    return render_template('challenge.html', ch=ch, solved=bool(solved))

# Таблица лидеров
@app.route('/scoreboard')
def scoreboard():
    with sqlite3.connect(DB) as con:
        board = con.execute('SELECT name, score FROM teams ORDER BY score DESC').fetchall()
    return render_template('scoreboard.html', board=board)

# Выход
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Статика
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
