import json
import os
import runpy
import subprocess
import sys
import tempfile

from checker import CheckResult, PATCH_ERROR

TASKS_DIR = "task_sources"
EDIT_START = "### НАЧАЛО БЛОКА РЕДАКТИРОВАНИЯ ###"
EDIT_END = "### КОНЕЦ БЛОКА РЕДАКТИРОВАНИЯ ###"


# Читает info.json из task_sources и обновляет задачи в БД.
def seed_tasks(db):
    from models import Task

    infos = []

    # Каждая папка в task_sources считается отдельной задачей, если в ней есть info.json.
    for folder in sorted(os.listdir(TASKS_DIR)):
        info_path = os.path.join(TASKS_DIR, folder, "info.json")
        if os.path.exists(info_path):
            with open(info_path, "r", encoding="utf-8") as file:
                infos.append(json.load(file))

    # Задачи, которые убрали из task_sources, скрываются из интерфейса.
    active_tasks = [info["task"] for info in infos]
    Task.query.filter(~Task.task.in_(active_tasks)).update(
        {"is_active": False},
        synchronize_session=False
    )

    for info in infos:
        # Если задача уже есть в базе, обновляем текст и вес из info.json.
        task = Task.query.filter_by(task=info["task"]).first()
        if not task:
            task = Task(task=info["task"])
            db.session.add(task)

        task.title = info["title"]
        task.description = info["description"]
        task.difficulty = info["difficulty"]
        task.category = info["category"]
        task.weight = info.get("weight", 100)
        task.source_path = os.path.join(TASKS_DIR, info["task"], "vuln.py")
        task.is_active = True

    db.session.commit()


# Возвращает код до блока, сам блок и код после блока.
def get_edit_block(code):
    # В файле должен быть ровно один блок редактирования.
    if code.count(EDIT_START) != 1 or code.count(EDIT_END) != 1:
        return None

    before, rest = code.split(EDIT_START)
    block, after = rest.split(EDIT_END)
    return before, block, after


# Собирает файл из оригинала и блока патча, затем запускает worker-процесс.
def check_patch(task, patch_path):
    try:
        # Читаем загруженный патч и оригинальный vuln.py задачи.
        with open(patch_path, "r", encoding="utf-8") as file:
            patch = file.read()
        with open(os.path.join(TASKS_DIR, task, "vuln.py"), "r", encoding="utf-8") as file:
            source = file.read()

        # Пользователь может менять только код между маркерами.
        source_parts = get_edit_block(source)
        patch_parts = get_edit_block(patch)
        if not source_parts or not patch_parts:
            return CheckResult(False, False, PATCH_ERROR)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Собираем временный файл: каркас берём из задачи, блок берём из патча.
            temp_patch = os.path.join(temp_dir, "patch.py")
            with open(temp_patch, "w", encoding="utf-8") as file:
                file.write(source_parts[0] + EDIT_START +
                           patch_parts[1] + EDIT_END + source_parts[2])

            # Запускаем checker в отдельном Python-процессе, чтобы не выполнять патч внутри Flask.
            result = subprocess.run([sys.executable, os.path.abspath(__file__),
                                     task, temp_patch],
                                    cwd=os.getcwd(),
                                    capture_output=True,
                                    text=True,
                                    timeout=8)
    except Exception:
        return CheckResult(False, False, PATCH_ERROR)

    if result.returncode != 0:
        return CheckResult(False, False, PATCH_ERROR)

    try:
        # Worker печатает один JSON, из него собирается общий CheckResult.
        data = json.loads(result.stdout)
        return CheckResult(data["availability_ok"],
                           data["security_ok"],
                           data["message"])
    except Exception:
        return CheckResult(False, False, PATCH_ERROR)


# Загружает checker.py задачи и печатает JSON-результат для основного процесса.
def run_worker(task, patch_path):
    # run_path загружает checker.py задачи как обычный Python-файл.
    checker_path = os.path.join(TASKS_DIR, task, "checker.py")
    checker = runpy.run_path(checker_path)

    # У каждого checker-а есть функция check(patch_path).
    result = checker["check"](patch_path)
    print(json.dumps(result.to_dict(), ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)
    run_worker(sys.argv[1], sys.argv[2])
