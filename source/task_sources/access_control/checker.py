from checker import CheckResult, PATCH_ERROR, load_patch


# Загружаем собранный файл и проверяем функцию на разных пользователях.
def check(patch_path):
    module = load_patch(patch_path)
    if isinstance(module, CheckResult):
        return module

    can_open_admin_panel = module.get("can_open_admin_panel")
    if not can_open_admin_panel:
        return CheckResult(False, False, "Функция can_open_admin_panel() не найдена.")

    try:
        real_admin = can_open_admin_panel({"username": "alice", "role": "admin"})
        fake_admin = can_open_admin_panel({"username": "admin", "role": "user"})
        usual_user = can_open_admin_panel({"username": "bob", "role": "user"})
    except Exception as error:
        if str(error) == PATCH_ERROR:
            return CheckResult(False, False, PATCH_ERROR)
        return CheckResult(False, False, f"Проверка доступа сломалась: {error}")

    availability_ok = real_admin is True
    security_ok = fake_admin is False and usual_user is False

    if not availability_ok:
        return CheckResult(False, False, "Настоящий администратор не получает доступ.")
    if not security_ok:
        return CheckResult(True, False, "Пользователь без роли admin получает доступ.")
    return CheckResult(True, True, "Патч принят: доступ зависит от роли.")
