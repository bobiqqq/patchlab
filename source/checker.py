import ast


PATCH_ERROR = "Патч не прошёл проверку."


class CheckResult:
    # Хранит итог проверки: работоспособность, безопасность и сообщение.
    def __init__(self, availability_ok, security_ok, message):
        self.availability_ok = availability_ok
        self.security_ok = security_ok
        self.message = message

    # Превращает два флага проверки в общий статус попытки.
    @property
    def status(self):
        if self.availability_ok and self.security_ok:
            return "patched"
        if self.availability_ok and not self.security_ok:
            return "vulnerable"
        return "broken"

    # Готовит результат для JSON-ответа.
    def to_dict(self):
        return {
            "status": self.status,
            "availability_ok": self.availability_ok,
            "security_ok": self.security_ok,
            "message": self.message
        }


# Разрешает патчу импортировать только учебные модули.
def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    # Проверяем основной модуль: для sqlite3.connect это будет sqlite3.
    base_name = name.split(".")[0]
    allowed_imports = {"sqlite3", "html", "secrets", "string", "flask"}

    # Всё, что не нужно учебным задачам, не даём импортировать.
    if base_name not in allowed_imports:
        raise ImportError(PATCH_ERROR)

    # Из Flask разрешаем только то, что уже используется в задачах.
    if base_name == "flask":
        for item in fromlist:
            if item not in {"Flask", "request"}:
                raise ImportError(PATCH_ERROR)

    return __import__(name, globals, locals, fromlist, level)


SAFE_BUILTINS = {
    "__import__": safe_import,
    "Exception": Exception,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "IndexError": IndexError,
    "len": len,
    "range": range,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "all": all,
    "any": any,
    "min": min,
    "max": max,
    "sum": sum,
}


# Делает короткую AST-проверку перед запуском патча.
def source_is_safe(source_code):
    # Эти имена чаще всего используются для выхода из простого sandbox-а.
    bad_names = {
        "__class__", "__bases__", "__mro__", "__subclasses__",
        "__globals__", "__builtins__", "__dict__", "__code__",
        "__import__", "__name__", "eval", "exec", "compile", "open",
        "input", "getattr", "setattr", "delattr", "vars", "locals",
        "globals"
    }

    try:
        # AST нужен, чтобы ловить не текст, а структуру Python-кода.
        tree = ast.parse(source_code)
    except SyntaxError:
        return False

    # Для учебного проекта достаточно простой проверки по dump дерева.
    tree_text = ast.dump(tree)
    if "Global(" in tree_text or "Nonlocal(" in tree_text:
        return False

    # Ищем запрещённые имена там, где AST хранит переменные и атрибуты.
    places = ("id", "attr", "name", "arg", "value")
    for name in bad_names:
        if any(f"{place}='{name}'" in tree_text for place in places):
            return False

    return True


# Читает, проверяет и выполняет собранный файл патча.
def load_patch(patch_path):
    try:
        # Здесь читается уже собранный временный файл, а не исходная загрузка пользователя.
        with open(patch_path, "r", encoding="utf-8") as patch_file:
            source_code = patch_file.read()
    except OSError:
        return CheckResult(False, False, PATCH_ERROR)

    if not source_code.strip():
        return CheckResult(False, False, PATCH_ERROR)

    if not source_is_safe(source_code):
        return CheckResult(False, False, PATCH_ERROR)

    # В патч попадают только выбранные builtins и безопасный импорт.
    patch_globals = {
        "__builtins__": SAFE_BUILTINS
    }

    try:
        # Код выполняется в отдельном словаре, а не в globals самого Flask.
        exec(compile(source_code, patch_path, "exec"), patch_globals)
    except Exception:
        return CheckResult(False, False, PATCH_ERROR)

    return patch_globals
