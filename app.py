from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import check_password_hash
import plotly.graph_objects as go
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'tomsox2025'

PITCH_COLORS = {
    "FB": "#E63946",
    "SL": "#457B9D",
    "CH": "#2A9D8F",
    "CB": "#E9C46A",
    "SNK": "#9B5DE5",
}


def get_db_connection():
    conn = sqlite3.connect('portalplayers.db')
    conn.row_factory = sqlite3.Row
    return conn


def parse_numeric_value(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip()
        if val == "":
            return None
        try:
            return float(val)
        except ValueError:
            pass
        if "-" in val:
            parts = val.split("-", 1)
            if len(parts) == 2:
                low, high = parts[0].strip(), parts[1].strip()
                try:
                    return (float(low) + float(high)) / 2
                except ValueError:
                    return None
    return None


def build_average_chart(data, pitch_cols, title, yaxis_title, yaxis_range, decimals=1, suffix=""):
    totals = {pitch: [] for pitch in pitch_cols}

    for row in data:
        for pitch, col in pitch_cols.items():
            numeric_val = parse_numeric_value(row[col])
            if numeric_val is not None:
                totals[pitch].append(numeric_val)

    pitches, avgs = [], []
    for pitch, values in totals.items():
        if values:
            pitches.append(pitch)
            avgs.append(round(sum(values) / len(values), decimals))

    if not pitches:
        return None

    fig = go.Figure()
    for pitch, avg in zip(pitches, avgs):
        label_value = f"{int(round(avg))}{suffix}" if decimals == 0 else f"{avg}{suffix}"
        fig.add_trace(go.Bar(
            x=[pitch], y=[avg], name=pitch,
            marker_color=PITCH_COLORS.get(pitch, "#888888"),
            text=[label_value], textposition="outside",
        ))

    fig.update_layout(
        title=title, xaxis_title="Pitch Type", yaxis_title=yaxis_title,
        yaxis=dict(range=yaxis_range), showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Arial", size=13),
        margin=dict(t=60, b=40, l=50, r=20),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eeeeee")
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def make_velocity_chart(data):
    return build_average_chart(
        data=data,
        pitch_cols={"FB": "FB_Velo_Avg", "SL": "SL_Velo_Avg", "CH": "CH_Velo_Avg",
                    "CB": "CB_Velo_Avg", "SNK": "SNK_Velo_Avg"},
        title="Avg Velocity by Pitch Type",
        yaxis_title="Velocity (mph)", yaxis_range=[60, 100], decimals=1, suffix=" mph"
    )


def make_spin_rate_chart(data):
    return build_average_chart(
        data=data,
        pitch_cols={"FB": "FB_Spin_Avg", "SL": "SL_Spin_Avg", "CH": "CH_Spin_Avg",
                    "CB": "CB_Spin_Avg", "SNK": "SNK_Spin_Avg"},
        title="Avg Spin Rate by Pitch Type",
        yaxis_title="Spin Rate (rpm)", yaxis_range=[1500, 2800], decimals=0, suffix=" rpm"
    )


def make_velo_over_season_chart(data):
    """
    Line chart: avg velocity per pitch type across dates (from averages table).
    One line per pitch type, x-axis = Date.
    """
    pitch_cols = {
        "FB": "FB_Velo_Avg",
        "SL": "SL_Velo_Avg",
        "CH": "CH_Velo_Avg",
        "CB": "CB_Velo_Avg",
        "SNK": "SNK_Velo_Avg",
    }

    # Collect (date, avg_velo) per pitch type, sorted by date
    pitch_series = defaultdict(list)  # pitch -> list of (date, value)

    for row in data:
        date = row["Date"]
        if not date:
            continue
        for pitch, col in pitch_cols.items():
            val = parse_numeric_value(row[col])
            if val is not None:
                pitch_series[pitch].append((date, val))

    if not pitch_series:
        return None

    fig = go.Figure()

    for pitch, points in pitch_series.items():
        points_sorted = sorted(points, key=lambda x: x[0])
        dates = [p[0] for p in points_sorted]
        velos = [p[1] for p in points_sorted]

        fig.add_trace(go.Scatter(
            x=dates, y=velos,
            mode="lines+markers",
            name=pitch,
            line=dict(color=PITCH_COLORS.get(pitch, "#888888"), width=2),
            marker=dict(size=7),
        ))

    fig.update_layout(
        title="Velocity by Pitch Type Over the Season",
        xaxis_title="Date",
        yaxis_title="Velocity (mph)",
        yaxis=dict(range=[60, 100]),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", size=13),
        margin=dict(t=60, b=40, l=50, r=20),
        legend=dict(title="Pitch Type"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eeeeee")

    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def make_velo_by_inning_chart(pitches_data):
    """
    Bar chart: avg velocity by inning, grouped by pitch type (from pitches table).
    Uses Inning and Velocity and Pitch columns.
    """
    # pitch -> inning -> list of velocities
    inning_velos = defaultdict(lambda: defaultdict(list))

    for row in pitches_data:
        pitch = row["Pitch"]
        inning = row["Inning"]
        velo = parse_numeric_value(row["Velocity"])

        if pitch is None:
            continue

        pitch = pitch.strip().upper()  # normalize here

        if pitch not in PITCH_COLORS:
            continue
        if inning is None or velo is None:
            continue

        try:
            inning_key = int(float(inning))
        except (ValueError, TypeError):
            continue

        inning_velos[pitch][inning_key].append(velo)

    if not inning_velos:
        return None

    # Collect all innings present across all pitches
    all_innings = sorted(set(
        inning
        for pitch_data in inning_velos.values()
        for inning in pitch_data.keys()
    ))

    fig = go.Figure()

    for pitch in PITCH_COLORS:
        if pitch not in inning_velos:
            continue
        avgs = []
        for inning in all_innings:
            vals = inning_velos[pitch].get(inning, [])
            avgs.append(round(sum(vals) / len(vals), 1) if vals else None)

        fig.add_trace(go.Bar(
            x=[str(i) for i in all_innings],
            y=avgs,
            name=pitch,
            marker_color=PITCH_COLORS[pitch],
        ))

    fig.update_layout(
        title="Avg Velocity by Inning",
        xaxis_title="Inning",
        yaxis_title="Velocity (mph)",
        yaxis=dict(range=[60, 100]),
        barmode="group",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", size=13),
        margin=dict(t=60, b=40, l=50, r=20),
        legend=dict(title="Pitch Type"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eeeeee")

    return fig.to_html(full_html=False, include_plotlyjs="cdn")

def make_strike_pct_trend_chart(game_data):
    """
    Line chart: strike % by game over the season.
    """
    print("DEBUG game_data rows:", [dict(row) for row in game_data])  # ADD THIS
    if not game_data:
        return None

    points = []
    for row in game_data:
        date = row["Date"]
        pct = parse_numeric_value(row["strike_pct"])
        if date and pct is not None:
            points.append((date, round(pct, 1)))

    if not points:
        return None

    points_sorted = sorted(points, key=lambda x: x[0])
    dates = [p[0] for p in points_sorted]
    pcts = [p[1] for p in points_sorted]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=pcts,
        mode="lines+markers",
        line=dict(color="#E63946", width=2),
        marker=dict(size=7),
        name="Strike %",
    ))

    # Reference line at 60% (generally considered a good benchmark)
    fig.add_hline(
        y=60,
        line_dash="dash",
        line_color="#aaaaaa",
        annotation_text="60% target",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title="Strike % by Game",
        xaxis_title="Date",
        yaxis_title="Strike %",
        yaxis=dict(range=[40, 80], ticksuffix="%"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", size=13),
        margin=dict(t=60, b=40, l=50, r=20),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eeeeee")

    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def make_strike_pct_by_pitch_chart(pitch_type_data):
    """
    Bar chart: strike % by pitch type for the season.
    """
    if not pitch_type_data:
        return None

    pitches, pcts = [], []
    for row in pitch_type_data:
        pitch = row["Pitch"]
        pct = parse_numeric_value(row["strike_pct"])
        if pitch and pct is not None:
            pitches.append(pitch.strip().upper())
            pcts.append(round(pct, 1))

    if not pitches:
        return None

    fig = go.Figure()
    for pitch, pct in zip(pitches, pcts):
        fig.add_trace(go.Bar(
            x=[pitch],
            y=[pct],
            name=pitch,
            marker_color=PITCH_COLORS.get(pitch, "#888888"),
            text=[f"{pct}%"],
            textposition="outside",
        ))

    fig.add_hline(
        y=60,
        line_dash="dash",
        line_color="#aaaaaa",
        annotation_text="60% target",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title="Strike % by Pitch Type (Season)",
        xaxis_title="Pitch Type",
        yaxis_title="Strike %",
        yaxis=dict(range=[0, 90], ticksuffix="%"),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", size=13),
        margin=dict(t=60, b=40, l=50, r=20),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eeeeee")

    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def make_first_strike_summary_chart(season_data):
    """
    Side-by-side bar: overall strike % vs first pitch strike % for the season.
    """
    if not season_data:
        return None

    row = season_data[0]
    strike_pct = parse_numeric_value(row["strike_pct"])
    first_strike_pct = parse_numeric_value(row["first_strike_pct"])

    if strike_pct is None or first_strike_pct is None:
        return None

    strike_pct = round(strike_pct, 1)
    first_strike_pct = round(first_strike_pct, 1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Overall Strike %"],
        y=[strike_pct],
        marker_color="#457B9D",
        text=[f"{strike_pct}%"],
        textposition="outside",
        name="Overall Strike %",
    ))
    fig.add_trace(go.Bar(
        x=["First Pitch Strike %"],
        y=[first_strike_pct],
        marker_color="#2A9D8F",
        text=[f"{first_strike_pct}%"],
        textposition="outside",
        name="First Pitch Strike %",
    ))

    fig.add_hline(
        y=60,
        line_dash="dash",
        line_color="#aaaaaa",
        annotation_text="60% target",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title="Season Strike % Summary",
        yaxis_title="Strike %",
        yaxis=dict(range=[0, 90], ticksuffix="%"),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", size=13),
        margin=dict(t=60, b=40, l=50, r=20),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eeeeee")

    return fig.to_html(full_html=False, include_plotlyjs="cdn")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session.pop('role', None)
            return redirect(url_for('dashboard'))

        return 'Invalid username or password'

    return render_template('login.html')


@app.route('/hitter_login', methods=['GET', 'POST'])
def hitter_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM hitting_users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['role'] = 'hitter'
            return redirect(url_for('hitter_dashboard'))

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

    if view == 'averages':
        data = conn.execute(
            'SELECT * FROM averages WHERE Pitcher = ?', (username,)
        ).fetchall()

        # Also pull pitches data for the inning chart
        pitches_data = conn.execute(
            'SELECT * FROM pitches WHERE Pitcher = ?', (username,)
        ).fetchall()

        conn.close()

        vel_chart = make_velocity_chart(data)
        spin_chart = make_spin_rate_chart(data)
        velo_season_chart = make_velo_over_season_chart(data)
        velo_inning_chart = make_velo_by_inning_chart(pitches_data)

        return render_template(
            'dashboard.html',
            data=data,
            current_view=view,
            announcement=announcement,
            vel_chart=vel_chart,
            spin_chart=spin_chart,
            velo_season_chart=velo_season_chart,
            velo_inning_chart=velo_inning_chart,
            strike_trend_chart=None,
            strike_pitch_chart=None,
            first_strike_chart=None,
        )

    elif view == 'strike_stats':
        game_data = conn.execute(
            'SELECT * FROM strike_stats_game WHERE Pitcher = ? ORDER BY Date', (username,)
        ).fetchall()
        season_data = conn.execute(
            'SELECT * FROM strike_stats_overall WHERE Pitcher = ?', (username,)
        ).fetchall()
        pitch_type_season = conn.execute(
            'SELECT * FROM strike_stats_pitch_type_overall WHERE Pitcher = ?', (username,)
        ).fetchall()
        conn.close()

        strike_trend_chart = make_strike_pct_trend_chart(game_data)
        strike_pitch_chart = make_strike_pct_by_pitch_chart(pitch_type_season)
        first_strike_chart = make_first_strike_summary_chart(season_data)

        return render_template(
            'dashboard.html',
            data=None,
            game_data=game_data,
            season_data=season_data,
            pitch_type_season=pitch_type_season,
            current_view=view,
            announcement=announcement,
            vel_chart=None,
            spin_chart=None,
            velo_season_chart=None,
            velo_inning_chart=None,
            strike_trend_chart=strike_trend_chart,
            strike_pitch_chart=strike_pitch_chart,
            first_strike_chart=first_strike_chart,

        )

    else:
        data = conn.execute(
            'SELECT * FROM pitches WHERE Pitcher = ?', (username,)
        ).fetchall()
        conn.close()

        return render_template(
            'dashboard.html',
            data=data,
            current_view=view,
            announcement=announcement,
            vel_chart=None,
            spin_chart=None,
            velo_season_chart=None,
            velo_inning_chart=None,
            strike_trend_chart=None,
            strike_pitch_chart=None,
            first_strike_chart=None,
        )


@app.route('/hitter_dashboard')
def hitter_dashboard():
    if 'username' not in session or session.get('role') != 'hitter':
        return redirect(url_for('hitter_login'))

    username = session['username']
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM hitting_stats WHERE Hitter = ?', (username,)).fetchall()
    conn.close()

    return render_template('hitter_dashboard.html', data=data)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)