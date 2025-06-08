from flask import Flask, render_template, redirect, url_for, request, session, flash
import mysql.connector
import hashlib
import json

app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)
app.secret_key = 'to_change'  # Change this in production

def get_db():
    return mysql.connector.connect(
        host="mysql.agh.edu.pl",
        user="akoncew1",
        password="EFq1FdGFBvf1PrgF",
        database="akoncew1"
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('tasks'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        if user and user['password_hash'] == hashlib.sha256(password.encode()).hexdigest():
            session['user_id'] = user['id']
            session['nick'] = user['nick']
            session['team_fk'] = user['team_fk']
            return redirect(url_for('tasks'))
        else:
            flash('Invalid login or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        email = request.form['email']
        password = request.form['password']
        nick = "Maciek"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (login, email, password_hash, nick) VALUES (%s, %s, %s, %s)",
                (login, email, password_hash, nick)
            )
            db.commit()
            cursor.close()
            db.close()
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Login already exists')
            cursor.close()
            db.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    user_id = session['user_id']
    # Fetch user and team info
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    team = None
    team_users = []
    is_leader = False
    notification_settings = {
        "new_task": False,
        "task_completed": False,
        "upcoming_deadline": False,
        "deadline_missed": False
    }
    # Load notification settings if present
    if user.get('notification_settings'):
        try:
            notification_settings.update(json.loads(user['notification_settings']))
        except Exception:
            pass
    if user['team_fk']:
        cursor.execute("SELECT * FROM team WHERE id=%s", (user['team_fk'],))
        team = cursor.fetchone()
        if team:
            is_leader = (team.get('owner') == user_id)
            cursor.execute("SELECT id, nick FROM users WHERE team_fk=%s", (user['team_fk'],))
            team_users = cursor.fetchall()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'join_team':
            team_code = request.form.get('team_code')
            cursor.execute("SELECT id FROM team WHERE invite_code=%s", (team_code,))
            found_team = cursor.fetchone()
            if found_team:
                cursor.execute("UPDATE users SET team_fk=%s WHERE id=%s", (found_team['id'], user_id))
                db.commit()
                session['team_fk'] = found_team['id']
                flash('Joined team successfully')
                # Refresh user/team info
                cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
                user = cursor.fetchone()
                cursor.execute("SELECT * FROM team WHERE id=%s", (user['team_fk'],))
                team = cursor.fetchone()
                if team:
                    is_leader = (team.get('owner') == user_id)
                    cursor.execute("SELECT id, nick FROM users WHERE team_fk=%s", (user['team_fk'],))
                    team_users = cursor.fetchall()
            else:
                flash('Invalid team code')
        elif action == 'change_team_name' and team and is_leader:
            new_name = request.form.get('team_name', '').strip()
            if new_name:
                cursor.execute("UPDATE team SET name=%s WHERE id=%s", (new_name, team['id']))
                db.commit()
                flash('Team name updated')
                team['name'] = new_name
        elif action == 'remove_member' and team and is_leader:
            remove_user_id = request.form.get('remove_user_id')
            if remove_user_id and str(remove_user_id) != str(user_id):
                cursor.execute("UPDATE users SET team_fk=NULL WHERE id=%s", (remove_user_id,))
                db.commit()
                flash('User removed from team')
                # Refresh team_users
                cursor.execute("SELECT id, nick FROM users WHERE team_fk=%s", (team['id'],))
                team_users = cursor.fetchall()
        elif action == 'save_settings':
            notification_settings = {
                "new_task": bool(request.form.get('notif_new_task')),
                "task_completed": bool(request.form.get('notif_task_completed')),
                "upcoming_deadline": bool(request.form.get('notif_upcoming_deadline')),
                "deadline_missed": bool(request.form.get('notif_deadline_missed'))
            }
            cursor.execute(
                "UPDATE users SET notification_settings=%s WHERE id=%s",
                (json.dumps(notification_settings), user_id)
            )
            db.commit()
            flash('Settings updated')
    cursor.close()
    db.close()
    return render_template(
        'settings.html',
        user=user,
        team=team,
        team_users=team_users,
        is_leader=is_leader,
        notification_settings=notification_settings
    )

@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    user_id = session['user_id']
    team_fk = session.get('team_fk')
    # Example stats: completed tasks by user, by team, etc.
    cursor.execute("SELECT COUNT(*) as completed FROM tasks WHERE assigned_user=%s AND status=1", (user_id,))
    completed = cursor.fetchone()['completed']
    cursor.execute("SELECT COUNT(*) as team_completed FROM tasks WHERE team_id=%s AND status=1", (team_fk,))
    team_completed = cursor.fetchone()['team_completed'] if team_fk else 0
    cursor.close()
    db.close()
    return render_template('stats.html', completed=completed, team_completed=team_completed)

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    user_id = session['user_id']
    team_fk = session.get('team_fk')
    if request.method == 'POST':
        # Example: create new task
        title = request.form.get('title')
        tags = request.form.get('tags', '[]')
        assigned_user = request.form.get('assigned_user')
        priority = int(request.form.get('priority', 1))
        cursor.execute(
            "INSERT INTO tasks (team_id, title, tags, assigned_user, priority) VALUES (%s, %s, %s, %s, %s)",
            (team_fk, title, tags, assigned_user, priority)
        )
        db.commit()
    # Load tasks for the user's team
    cursor.execute(
        "SELECT t.*, u.nick as assigned_nick FROM tasks t LEFT JOIN users u ON t.assigned_user=u.id WHERE t.team_id=%s",
        (team_fk,)
    )
    tasks = cursor.fetchall()
    cursor.execute("SELECT id, nick FROM users WHERE team_fk=%s", (team_fk,))
    team_users = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('tasks.html', tasks=tasks, team_users=team_users)

if __name__ == '__main__':
    app.run(debug=True)
