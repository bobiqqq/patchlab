import json
import os
import runpy
import subprocess
import sys
import tempfile

from checker import CheckResult, PATCH_ERROR

TASKS_DIR = "task_sources"
EDIT_MARK = "### БЛОК РЕДАКТИРОВАНИЯ ###"


def seed_tasks(db):
    # Читает info.json из task_sources и обновляет задачи в БД.
    from models import Task

    infos = []
    for folder in sorted(os.listdir(TASKS_DIR)):
        info_path = os.path.join(TASKS_DIR, folder, "info.json")
        if os.path.exists(info_path):
            with open(info_path, "r", encoding="utf-8") as file:
                infos.append(json.load(file))

    active_tasks = [info["task"] for info in infos]
    Task.query.filter(~Task.task.in_(active_tasks)).update(
        {"is_active": False},
        synchronize_session=False
    )

    for info in infos:
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


def get_edit_block(code):
    # Возвращает код до блока, сам блок и код после блока.
    if code.count(EDIT_MARK) != 2:
        return None

    before, block, after = code.split(EDIT_MARK)
    return before, block, after


def check_patch(task, patch_path):
    # Собирает файл из оригинала и блока патча, затем запускает worker-процесс.
    try:
        with open(patch_path, "r", encoding="utf-8") as file:
            patch = file.read()
        with open(os.path.join(TASKS_DIR, task, "vuln.py"), "r", encoding="utf-8") as file:
            source = file.read()

        source_parts = get_edit_block(source)
        patch_parts = get_edit_block(patch)
        if not source_parts or not patch_parts:
            return CheckResult(False, False, PATCH_ERROR)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_patch = os.path.join(temp_dir, "patch.py")
            with open(temp_patch, "w", encoding="utf-8") as file:
                file.write(source_parts[0] + EDIT_MARK +
                           patch_parts[1] + EDIT_MARK + source_parts[2])

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
        data = json.loads(result.stdout)
        return CheckResult(data["availability_ok"],
                           data["security_ok"],
                           data["message"])
    except Exception:
        return CheckResult(False, False, PATCH_ERROR)


def run_worker(task, patch_path):
    # Загружает checker.py задачи и печатает JSON-результат для основного процесса.
    checker_path = os.path.join(TASKS_DIR, task, "checker.py")
    checker = runpy.run_path(checker_path)
    result = checker["check"](patch_path)
    print(json.dumps(result.to_dict(), ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)
    run_worker(sys.argv[1], sys.argv[2])
