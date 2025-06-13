from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, get_flashed_messages
import mysql.connector
import hashlib
import json
from datetime import datetime, timedelta

app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)
app.secret_key = 'to_change'  # Change this in production

# Add this filter after app creation
@app.template_filter('from_json')
def from_json_filter(s):
    try:
        return json.loads(s)
    except Exception:
        return []

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
                flash('Joined team successfully', 'success')
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
                flash('Invalid team code', 'error')
        elif action == 'change_team_name' and team and is_leader:
            new_name = request.form.get('team_name', '').strip()
            if new_name:
                cursor.execute("UPDATE team SET name=%s WHERE id=%s", (new_name, team['id']))
                db.commit()
                flash('Team name updated', 'success')
                team['name'] = new_name
        elif action == 'change_invite_code' and team and is_leader:
            new_code = request.form.get('invite_code', '').strip()
            if new_code:
                cursor.execute("UPDATE team SET invite_code=%s WHERE id=%s", (new_code, team['id']))
                db.commit()
                flash('Invite code updated', 'success')
                team['invite_code'] = new_code
            else:
                flash('Invite code cannot be empty', 'error')
        elif action == 'remove_member' and team and is_leader:
            remove_user_id = request.form.get('remove_user_id')
            if remove_user_id and str(remove_user_id) != str(user_id):
                cursor.execute("UPDATE users SET team_fk=NULL WHERE id=%s", (remove_user_id,))
                db.commit()
                flash('User removed from team', 'success')
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
            flash('Settings updated', 'success')
    cursor.close()
    db.close()
    return render_template(
        'settings.html',
        user=user,
        team=team,
        team_users=team_users,
        is_leader=is_leader,
        notification_settings=notification_settings,
        messages=get_flashed_messages(with_categories=True)
    )

@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    user_id = session['user_id']
    team_fk = session.get('team_fk')

    # Completed tasks for this user
    cursor.execute("SELECT title, completion_date FROM tasks WHERE assigned_user=%s AND status=1", (user_id,))
    user_completed_tasks = cursor.fetchall()

    # Completed tasks for this team
    team_completed = 0
    if team_fk:
        cursor.execute("SELECT COUNT(*) as team_completed FROM tasks WHERE team_id=%s AND status=1", (team_fk,))
        team_completed = cursor.fetchone()['team_completed']

    # Calculate stats for today, this week, this month
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    completed_today = 0
    completed_week = 0
    completed_month = 0
    completed_titles = []

    for task in user_completed_tasks:
        if task['completion_date']:
            comp_date = task['completion_date']
            if isinstance(comp_date, str):
                comp_date = datetime.strptime(comp_date, "%Y-%m-%d").date()
            if comp_date == today:
                completed_today += 1
            if comp_date >= week_start:
                completed_week += 1
            if comp_date >= month_start:
                completed_month += 1
            completed_titles.append(task['title'])

    cursor.close()
    db.close()
    return render_template(
        'stats.html',
        completed_titles=completed_titles,
        completed_today=completed_today,
        completed_week=completed_week,
        completed_month=completed_month,
        team_completed=team_completed
    )

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    user_id = session['user_id']

    # Dodawanie nowego taska przez AJAX
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        # Dodawanie taska
        if data.get('add_task'):
            title = data.get('title', '').strip()
            priority = data.get('priority')
            tags = data.get('tags', '')
            assigned_user = data.get('assigned_user')
            completion_date = data.get('completion_date')
            team_fk = session.get('team_fk')
            # Walidacja
            if not (title and priority and assigned_user and team_fk):
                cursor.close()
                db.close()
                return jsonify(success=False, error="Missing required fields"), 400
            try:
                priority = int(priority)
                if priority < 1 or priority > 4:
                    raise ValueError
            except Exception:
                cursor.close()
                db.close()
                return jsonify(success=False, error="Invalid priority"), 400
            # Sprawdź czy assigned_user należy do teamu
            cursor.execute("SELECT id FROM users WHERE id=%s AND team_fk=%s", (assigned_user, team_fk))
            if not cursor.fetchone():
                cursor.close()
                db.close()
                return jsonify(success=False, error="User not in your team"), 400
            # Przetwórz tagi
            tags_list = [t.strip() for t in tags.split(',') if t.strip()]
            tags_json = json.dumps(tags_list)
            # Data
            if completion_date:
                try:
                    datetime.strptime(completion_date, "%Y-%m-%d")
                except Exception:
                    cursor.close()
                    db.close()
                    return jsonify(success=False, error="Invalid date"), 400
            else:
                completion_date = None
            # Dodaj taska
            cursor.execute(
                "INSERT INTO tasks (team_id, title, status, completion_date, tags, assigned_user, priority) VALUES (%s, %s, 0, %s, %s, %s, %s)",
                (team_fk, title, completion_date, tags_json, assigned_user, priority)
            )
            db.commit()
            cursor.close()
            db.close()
            return jsonify(success=True)
        # ...istniejąca obsługa zmiany statusu...
        task_id = data.get('task_id')
        new_status = data.get('status')
        if task_id is not None and new_status in (0, 1, True, False):
            if new_status:
                # Mark as completed and set completion_date to now
                cursor.execute(
                    "UPDATE tasks SET status=1, completion_date=%s WHERE id=%s AND assigned_user=%s",
                    (datetime.now().date(), task_id, user_id)
                )
            else:
                # Mark as not completed and clear completion_date
                cursor.execute(
                    "UPDATE tasks SET status=0, completion_date=NULL WHERE id=%s AND assigned_user=%s",
                    (task_id, user_id)
                )
            db.commit()
            cursor.close()
            db.close()
            return jsonify(success=True)
        cursor.close()
        db.close()
        return jsonify(success=False), 400

    # Get all tasks assigned to this user, order unfinished first
    cursor.execute(
        "SELECT t.*, u.nick as assigned_nick FROM tasks t LEFT JOIN users u ON t.assigned_user=u.id WHERE t.assigned_user=%s ORDER BY t.status ASC, t.id ASC",
        (user_id,)
    )
    tasks = cursor.fetchall()
    cursor.execute("SELECT id, nick FROM users WHERE team_fk=%s", (session.get('team_fk'),))
    team_users = cursor.fetchall()
    # Dodaj pobranie teamu użytkownika
    team = None
    if session.get('team_fk'):
        cursor.execute("SELECT * FROM team WHERE id=%s", (session.get('team_fk'),))
        team = cursor.fetchone()
    cursor.close()
    db.close()
    return render_template('tasks.html', tasks=tasks, team_users=team_users, team=team)

if __name__ == '__main__':
    app.run(debug=True)
