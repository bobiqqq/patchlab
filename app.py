import os
from flask import (Flask, Blueprint, render_template, redirect, url_for,
                   request, flash, abort, send_file)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from api import api_bp
from models import (db, User, Task, Patch)
from tasks_methods import seed_tasks

login_manager = LoginManager()

auth_bp = Blueprint('auth', __name__)
dashboard_bp = Blueprint('dashboard', __name__)
tasks_bp = Blueprint('tasks', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Заполните имя пользователя и пароль.')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Такое имя пользователя уже занято.')
            return redirect(url_for('auth.register'))

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard.index'))
        flash('Неверное имя пользователя или пароль.')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('dashboard.home'))


@dashboard_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')


@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Показывает список задач и историю попыток текущего пользователя.
    patches = Patch.query.filter_by(user_id=current_user.id).order_by(Patch.created_at.desc()).all()
    patched_count = Patch.query.filter_by(user_id=current_user.id, status='patched').count()
    total_score = sum(patch.score for patch in patches)
    return render_template('dashboard.html',
                           tasks=Task.query.filter_by(is_active=True).all(),
                           patches=patches,
                           patched_count=patched_count,
                           total_score=total_score)


@tasks_bp.route('/tasks/<task>', endpoint='detail')
@login_required
def task_detail(task):
    # Показывает страницу задачи, исходник и попытки пользователя по этой задаче.
    task = Task.query.filter_by(task=task).first_or_404()
    patches = Patch.query.filter_by(user_id=current_user.id, task_id=task.id).order_by(Patch.created_at.desc()).all()
    return render_template('task_detail.html',
                           task=task,
                           patches=patches,
                           source_content=read_source(task.source_path))


@tasks_bp.route('/tasks/<task>/source')
@login_required
def download_source(task):
    # Отдаёт пользователю исходный код выбранной задачи.
    task = Task.query.filter_by(task=task).first_or_404()
    source_path = os.path.join(os.getcwd(), task.source_path)
    if not os.path.exists(source_path):
        abort(404, description="Исходный файл не найден")
    return send_file(source_path, as_attachment=True, download_name='vuln.py')


def read_source(path, absolute=False):
    # Читает исходник задачи для показа прямо на странице.
    source_path = path if absolute else os.path.join(os.getcwd(), path)
    if not source_path or not os.path.exists(source_path):
        return "Файл не найден."
    with open(source_path, "r", encoding="utf-8") as source_file:
        return source_file.read()


def create_app():
    # Создаёт Flask-приложение, подключает БД, blueprints и задачи.
    app = Flask(__name__)
    data_dir = os.path.join(os.getcwd(), 'data')
    os.makedirs(data_dir, exist_ok=True)

    app.config['SECRET_KEY'] = 'patchlab-secret-key-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(data_dir, 'patchlab.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        seed_tasks(db)

    return app
