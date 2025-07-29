from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tomsox2025'

def get_db_connection():
    conn = sqlite3.connect('portalplayers.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', 
(username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/hitter_login', methods=['GET', 'POST'])
def hitter_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * from hitting_users WHERE username = ?',
(username, )).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['role'] = 'hitter'
            return redirect(url_for('hitter_dashboard'))
        else:
            return 'Invalid username or password'
    return render_template('hitter_login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']   
    view = request.args.get('view', 'pitches')

    announcement = 'Radar gun was off center for game 7/28. Velos under by 2-3 mph.'

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row

    if view == 'averages':
        data = conn.execute(
            'SELECT * FROM averages WHERE Pitcher = ?',
            (username,)
        ).fetchall()
        conn.close()
        return render_template('dashboard.html', data=data, current_view=view, announcement=announcement)

    elif view == 'strike_stats':
        game_data = conn.execute(
            'SELECT * FROM strike_stats_game WHERE Pitcher = ? ORDER by Date',
            (username,)
        ).fetchall()
        season_data = conn.execute(
            'SELECT * FROM strike_stats_overall WHERE Pitcher = ?',
            (username,)
        ).fetchall()
        pitch_type_season = conn.execute(
            'SELECT * FROM strike_stats_pitch_type_overall WHERE Pitcher = ?',
            (username,)
        ).fetchall()
        conn.close()
        return render_template('dashboard.html',
            data=None,
            game_data=game_data,
            season_data=season_data,
            pitch_type_season=pitch_type_season,
            current_view=view,
            announcement=announcement
        )


    else:
        data = conn.execute(
            'SELECT * FROM pitches WHERE Pitcher = ?',
            (username,)
        ).fetchall()
        conn.close()
        return render_template('dashboard.html', data=data, current_view=view, announcement=announcement)

@app.route('/hitter_dashboard')
def hitter_dashboard():
    if 'username' not in session or session.get('role') != 'hitter':
        return redirect(url_for('hitter_login'))

    username = session['username']
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    data = conn.execute(
        'SELECT * FROM hitting_stats WHERE Hitter = ?', (username,)
    ).fetchall()
    conn.close()

    return render_template('hitter_dashboard.html', data=data)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

