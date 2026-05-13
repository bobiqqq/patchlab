from checker import CheckResult, PATCH_ERROR, load_patch


def check(patch_path):
    # Проверяет, что заметка выводится и XSS payload экранируется.
    module = load_patch(patch_path)
    if isinstance(module, CheckResult):
        return module

    app = module.get("app")
    show_note = module.get("show_note")
    if not app or not show_note:
        return CheckResult(False, False, "В патче должны быть app и show_note().")

    try:
        with app.test_request_context("/note?note=hello"):
            normal_response = show_note()

        payload = "<script>alert(1)</script>"
        with app.test_request_context("/note?note=" + payload):
            attack_response = show_note()
    except Exception as error:
        if str(error) == PATCH_ERROR:
            return CheckResult(False, False, PATCH_ERROR)
        return CheckResult(False, False, f"Маршрут заметки сломан: {error}")

    availability_ok = "hello" in normal_response
    security_ok = "<script>" not in attack_response and "&lt;script&gt;" in attack_response

    if not availability_ok:
        return CheckResult(False, False, "Обычная заметка не выводится.")
    if not security_ok:
        return CheckResult(True, False, "XSS payload попадает в HTML без экранирования.")
    return CheckResult(True, True, "Патч принят: XSS payload экранируется.")
