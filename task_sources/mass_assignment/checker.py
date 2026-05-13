from checker import CheckResult, PATCH_ERROR, load_patch


def check(patch_path):
    # Проверяет, что профиль обновляет только разрешённые поля.
    module = load_patch(patch_path)
    if isinstance(module, CheckResult):
        return module

    update_profile = module.get("update_profile")
    if not update_profile:
        return CheckResult(False, False, "Функция update_profile() не найдена.")

    user = {"username": "bob", "role": "user", "display_name": "Bob", "bio": ""}
    data = {"display_name": "Bobby", "bio": "hello", "role": "admin"}

    try:
        updated = update_profile(user.copy(), data)
    except Exception as error:
        if str(error) == PATCH_ERROR:
            return CheckResult(False, False, PATCH_ERROR)
        return CheckResult(False, False, f"Обновление профиля сломалось: {error}")

    availability_ok = updated.get("display_name") == "Bobby" and updated.get("bio") == "hello"
    security_ok = updated.get("role") == "user"

    if not availability_ok:
        return CheckResult(False, False, "Безопасные поля профиля не обновляются.")
    if not security_ok:
        return CheckResult(True, False, "Поле role всё ещё можно изменить.")
    return CheckResult(True, True, "Патч принят: роль не меняется через data.")
