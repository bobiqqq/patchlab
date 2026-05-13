import os

from flask import (Blueprint, request, jsonify, current_app)
from flask_login import (login_required, current_user)
from werkzeug import utils

from models import (Task, Patch, db)
from tasks_methods import check_patch

api_bp = Blueprint('api', __name__)


def score_from_result(result, weight=100):
    # Переводит результат checker-а в очки за попытку.
    if result.status == "patched":
        return weight
    if result.status == "vulnerable":
        return int(weight * 0.4)
    return 0


@api_bp.route('/api/tasks')
@login_required
def get_tasks():
    # Возвращает активные задачи для API.
    tasks = Task.query.filter_by(is_active=True).all()
    return jsonify([{"task": task.task, "title": task.title} for task in tasks])


@api_bp.route('/api/tasks/<task>/check', methods=['POST'])
@login_required
def check_task(task):
    # Принимает файл патча, запускает проверку и сохраняет попытку.
    task = Task.query.filter_by(task=task).first_or_404()

    if 'patch' not in request.files:
        return jsonify({"error": "Файл патча не передан"}), 400

    file = request.files['patch']
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    if not file.filename.endswith('.py') and not file.filename.endswith('.txt'):
        return jsonify({"error": "Можно загрузить только .py или .txt файл"}), 400

    # Очистка пути файла до безопасного вида
    filename = utils.secure_filename(file.filename)
    user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'],
                            str(current_user.id), task.task)
    os.makedirs(user_dir, exist_ok=True)

    file_path = os.path.join(user_dir, filename)
    file.save(file_path)

    result = check_patch(task.task, file_path)
    score = score_from_result(result, task.weight)

    # Каждая загрузка сразу становится отдельной попыткой решения.
    patch = Patch(user_id=current_user.id,
                  task_id=task.id,
                  filename=filename,
                  file_path=file_path,
                  status=result.status,
                  score=score,
                  checker_output=result.message)
    db.session.add(patch)
    db.session.commit()

    data = result.to_dict()
    data["score"] = score
    data["patch_id"] = patch.id
    return jsonify(data)
