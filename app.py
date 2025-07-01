from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tomsox2025'  # Replace with a real secret key

def get_db_connection():
    conn = sqlite3.connect('portalplayers.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return redirect(url_for('login'))

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

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']   
    view = request.args.get('view', 'pitches')

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row

    if view == 'averages':
        data = conn.execute(
            'SELECT * FROM averages WHERE Pitcher = ?',
            (username,)
        ).fetchall()
        conn.close()
        return render_template('dashboard.html', data=data, current_view=view)

    elif view == 'strike_stats':
        game_data = conn.execute(
            'SELECT * FROM strike_stats_game WHERE Pitcher = ?',
            (username,)
        ).fetchall()
        season_data = conn.execute(
            'SELECT * FROM strike_stats_overall WHERE Pitcher = ?',
            (username,)
        ).fetchall()
        conn.close()
        return render_template(
            'dashboard.html',
            game_data=game_data,
            season_data=season_data,
            current_view=view
        )

    else:
        data = conn.execute(
            'SELECT * FROM pitches WHERE Pitcher = ?',
            (username,)
        ).fetchall()
        conn.close()
        return render_template('dashboard.html', data=data, current_view=view)



@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

