from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
import sqlite3, json, os

app = Flask(__name__)
app.secret_key = 'secret123'
DB = 'db.sqlite3'

def init_db():
    with sqlite3.connect(DB) as con:
        c = con.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY, name TEXT, password TEXT, score INTEGER DEFAULT 0)')
        c.execute('CREATE TABLE IF NOT EXISTS solves (id INTEGER PRIMARY KEY, team_id INTEGER, challenge TEXT)')
        con.commit()

with open('tasks.json', encoding='utf-8') as f:
    TASKS = json.load(f)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/tasks')
def tasks():
    if 'team' not in session:
        return redirect('/login')
    return render_template('tasks.html', tasks=TASKS)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        with sqlite3.connect(DB) as con:
            con.execute('INSERT INTO teams (name, password) VALUES (?, ?)', (name, password))
        return redirect('/login')
    return render_template('register.html')

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
    return render_template('login.html')

@app.route('/challenge/<id>', methods=['GET', 'POST'])
def challenge(id):
    if 'team' not in session:
        return redirect('/login')
    ch = TASKS.get(id)
    solved = False
    with sqlite3.connect(DB) as con:
        c = con.cursor()
        c.execute('SELECT * FROM solves WHERE team_id=? AND challenge=?', (session['team'], id))
        solved = c.fetchone()
        if request.method == 'POST' and not solved:
            if request.form['flag'] == ch['flag']:
                c.execute('INSERT INTO solves (team_id, challenge) VALUES (?, ?)', (session['team'], id))
                c.execute('UPDATE teams SET score = score + ? WHERE id = ?', (ch['value'], session['team']))
                con.commit()
                return render_template('challenge.html', ch=ch, correct=True)
            else:
                return render_template('challenge.html', ch=ch, incorrect=True)
    return render_template('challenge.html', ch=ch, solved=bool(solved))

@app.route('/scoreboard')
def scoreboard():
    with sqlite3.connect(DB) as con:
        board = con.execute('SELECT name, score FROM teams ORDER BY score DESC').fetchall()
    return render_template('scoreboard.html', board=board)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)