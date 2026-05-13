import ast


PATCH_ERROR = "Патч не прошёл проверку."


class CheckResult:
    def __init__(self, availability_ok, security_ok, message):
        # Хранит итог проверки: работоспособность, безопасность и сообщение.
        self.availability_ok = availability_ok
        self.security_ok = security_ok
        self.message = message

    @property
    def status(self):
        # Превращает два флага проверки в общий статус попытки.
        if self.availability_ok and self.security_ok:
            return "patched"
        if self.availability_ok and not self.security_ok:
            return "vulnerable"
        return "broken"

    def to_dict(self):
        # Готовит результат для JSON-ответа.
        return {
            "status": self.status,
            "availability_ok": self.availability_ok,
            "security_ok": self.security_ok,
            "message": self.message
        }


def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    # Разрешает патчу импортировать только учебные модули.
    base_name = name.split(".")[0]
    allowed_imports = {"sqlite3", "html", "secrets", "string", "flask"}

    if base_name not in allowed_imports:
        raise ImportError(PATCH_ERROR)
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


def source_is_safe(source_code):
    # Делает короткую AST-проверку перед запуском патча.
    bad_names = {
        "__class__", "__bases__", "__mro__", "__subclasses__",
        "__globals__", "__builtins__", "__dict__", "__code__",
        "__import__", "__name__", "eval", "exec", "compile", "open",
        "input", "getattr", "setattr", "delattr", "vars", "locals",
        "globals"
    }

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return False

    tree_text = ast.dump(tree)
    if "Global(" in tree_text or "Nonlocal(" in tree_text:
        return False

    places = ("id", "attr", "name", "arg", "value")
    for name in bad_names:
        if any(f"{place}='{name}'" in tree_text for place in places):
            return False

    return True


def load_patch(patch_path):
    # Читает, проверяет и выполняет собранный файл патча.
    try:
        with open(patch_path, "r", encoding="utf-8") as patch_file:
            source_code = patch_file.read()
    except OSError:
        return CheckResult(False, False, PATCH_ERROR)

    if not source_code.strip():
        return CheckResult(False, False, PATCH_ERROR)

    if not source_is_safe(source_code):
        return CheckResult(False, False, PATCH_ERROR)

    patch_globals = {
        "__builtins__": SAFE_BUILTINS
    }

    try:
        exec(compile(source_code, patch_path, "exec"), patch_globals)
    except Exception:
        return CheckResult(False, False, PATCH_ERROR)

    return patch_globals
