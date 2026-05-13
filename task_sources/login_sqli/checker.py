import sqlite3

from checker import CheckResult, PATCH_ERROR, load_patch


def check(patch_path):
    # Проверяет, что login работает и не пропускает SQL-инъекции.
    module = load_patch(patch_path)
    if isinstance(module, CheckResult):
        return module

    login = module.get("login")
    if not login:
        return CheckResult(False, False, "В патче не найдена функция login().")

    old_connect = sqlite3.connect
    db_uri = "file:patchlab_login_check?mode=memory&cache=shared"
    keeper = old_connect(db_uri, uri=True)

    def test_connect(name):
        # Подменяет подключение так, чтобы патч работал с тестовой in-memory БД.
        return old_connect(db_uri, uri=True)

    try:
        sqlite3.connect = test_connect
        cursor = keeper.cursor()
        cursor.execute("CREATE TABLE users (username TEXT, password TEXT)")
        cursor.execute("INSERT INTO users VALUES (?, ?)", ("admin", "secret"))
        cursor.execute("INSERT INTO users VALUES (?, ?)", ("alice", "qwerty"))
        keeper.commit()

        ok_login = login("admin", "secret")
        bad_password = login("admin", "wrong")
        sqli_comment = login("admin' --", "wrong")
        sqli_or = login("' OR '1'='1' --", "wrong")
    except Exception as error:
        if str(error) == PATCH_ERROR:
            return CheckResult(False, False, PATCH_ERROR)
        return CheckResult(False, False, f"Функция login() сломалась: {error}")
    finally:
        sqlite3.connect = old_connect
        keeper.close()

    availability_ok = bool(ok_login) and not bad_password
    security_ok = not sqli_comment and not sqli_or

    if not availability_ok:
        return CheckResult(False, False, "Обычный вход сломан.")
    if not security_ok:
        return CheckResult(True, False, "SQL-инъекция всё ещё проходит.")
    return CheckResult(True, True, "Патч принят: SQL-инъекция не проходит.")
