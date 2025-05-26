from flask import Flask, render_template, redirect, url_for, request

app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)
# todo app.secret_key = 'to_change'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # todo authenticate user here
        return redirect(url_for('tasks'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # todo register user here
        return redirect(url_for('tasks'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    # todo clear user session here
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # todo load and save settings
    return render_template('settings.html')

@app.route('/stats')
def stats():
    # todo get user/team stats
    return render_template('stats.html')

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    # todo load tasks, handle new task creation/completion
    return render_template('tasks.html')

if __name__ == '__main__':
    app.run(debug=True)
