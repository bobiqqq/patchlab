import os

from flask import (Blueprint, request, jsonify, current_app)
from flask_login import (login_required, current_user)
from werkzeug import utils

from models import (Task, Patch, db)
from tasks_methods import check_patch

api_bp = Blueprint('api', __name__)


# Переводит результат checker-а в очки за попытку.
def score_from_result(result, weight=100):
    # Полный вес даём только за исправленный и рабочий патч.
    if result.status == "patched":
        return weight

    # Если сервис работает, но уязвимость осталась, попытка всё равно частично засчитывается.
    if result.status == "vulnerable":
        return int(weight * 0.4)

    return 0


# Возвращает активные задачи для API.
@api_bp.route('/api/tasks')
@login_required
def get_tasks():
    # API отдаёт только включённые задачи, чтобы старые задачи не появлялись в интерфейсе.
    tasks = Task.query.filter_by(is_active=True).all()
    return jsonify([{"task": task.task, "title": task.title} for task in tasks])


# Принимает файл патча, запускает проверку и сохраняет попытку.
@api_bp.route('/api/tasks/<task>/check', methods=['POST'])
@login_required
def check_task(task):
    # Ищем задачу по её id из адреса /api/tasks/<task>/check.
    task = Task.query.filter_by(task=task).first_or_404()

    # Файл приходит из формы под именем patch.
    if 'patch' not in request.files:
        return jsonify({"error": "Файл патча не передан"}), 400

    file = request.files['patch']

    # Пустое имя обычно значит, что пользователь не выбрал файл.
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    # На этом этапе принимаем только текстовые Python-файлы.
    if not file.filename.endswith('.py') and not file.filename.endswith('.txt'):
        return jsonify({"error": "Можно загрузить только .py или .txt файл"}), 400

    # Очистка пути файла до безопасного вида.
    filename = utils.secure_filename(file.filename)

    # У каждого пользователя и каждой задачи своя папка с загруженными патчами.
    user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'],
                            str(current_user.id), task.task)
    os.makedirs(user_dir, exist_ok=True)

    # Сохраняем оригинальный загруженный файл, чтобы потом видеть историю попыток.
    file_path = os.path.join(user_dir, filename)
    file.save(file_path)

    # Checker собирает итоговый файл и проверяет его отдельным процессом.
    result = check_patch(task.task, file_path)
    score = score_from_result(result, task.weight)

    # Пишем результат попытки в базу для истории на странице задачи.
    patch = Patch(user_id=current_user.id,
                  task_id=task.id,
                  filename=filename,
                  file_path=file_path,
                  status=result.status,
                  score=score,
                  checker_output=result.message)
    db.session.add(patch)
    db.session.commit()

    # Возвращаем фронту и технический результат, и начисленные очки.
    data = result.to_dict()
    data["score"] = score
    data["patch_id"] = patch.id
    return jsonify(data)
