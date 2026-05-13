from checker import CheckResult, PATCH_ERROR, load_patch


# Проверяет, что функция читает только страницы из pages.
def check(patch_path):
    module = load_patch(patch_path)
    if isinstance(module, CheckResult):
        return module

    read_page = module.get("read_page")
    if not read_page:
        return CheckResult(False, False, "Функция read_page() не найдена.")

    storage = {
        "pages/about.txt": "about page",
        "pages/help.txt": "help page",
        "secret.txt": "private key",
        "pages/../secret.txt": "wrong path"
    }

    try:
        about = read_page("about.txt", storage)
        help_page = read_page("help.txt", storage)
        secret = read_page("secret.txt", storage)
        traversal = read_page("../secret.txt", storage)
        absolute = read_page("/secret.txt", storage)
    except Exception as error:
        if str(error) == PATCH_ERROR:
            return CheckResult(False, False, PATCH_ERROR)
        return CheckResult(False, False, f"Чтение страницы сломалось: {error}")

    availability_ok = about == "about page" and help_page == "help page"
    security_ok = not secret and not traversal and not absolute

    if not availability_ok:
        return CheckResult(False, False, "Обычные страницы не читаются.")
    if not security_ok:
        return CheckResult(True, False, "Файл вне pages всё ещё можно прочитать.")
    return CheckResult(True, True, "Патч принят: чтение ограничено каталогом pages.")
