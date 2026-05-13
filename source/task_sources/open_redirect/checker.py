from checker import CheckResult, PATCH_ERROR, load_patch


# Проверяет, что redirect разрешает только локальные пути.
def check(patch_path):
    module = load_patch(patch_path)
    if isinstance(module, CheckResult):
        return module

    is_safe_redirect = module.get("is_safe_redirect")
    if not is_safe_redirect:
        return CheckResult(False, False, "Функция is_safe_redirect() не найдена.")

    try:
        local_path = is_safe_redirect("/profile")
        full_url = is_safe_redirect("https://evil.example/login")
        protocol_relative = is_safe_redirect("//evil.example")
        script_url = is_safe_redirect("javascript:alert(1)")
    except Exception as error:
        if str(error) == PATCH_ERROR:
            return CheckResult(False, False, PATCH_ERROR)
        return CheckResult(False, False, f"Проверка redirect сломалась: {error}")

    availability_ok = local_path is True
    security_ok = full_url is False and protocol_relative is False and script_url is False

    if not availability_ok:
        return CheckResult(False, False, "Локальный redirect не проходит.")
    if not security_ok:
        return CheckResult(True, False, "Внешний redirect всё ещё проходит.")
    return CheckResult(True, True, "Патч принят: внешний redirect не проходит.")
