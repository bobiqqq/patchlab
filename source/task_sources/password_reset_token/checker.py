from checker import CheckResult, PATCH_ERROR, load_patch


# Проверяет, что reset-token работает, но не угадывается по данным пользователя.
def check(patch_path):
    module = load_patch(patch_path)
    if isinstance(module, CheckResult):
        return module

    make_reset_token = module.get("make_reset_token")
    verify_reset_token = module.get("verify_reset_token")
    if not make_reset_token or not verify_reset_token:
        return CheckResult(False, False, "Функции reset-token не найдены.")

    user = {"id": 7, "username": "alice", "reset_token": ""}
    guessed = "7-alice"

    try:
        token = make_reset_token(user)
        correct_token = verify_reset_token(user, token)
        wrong_token = verify_reset_token(user, "wrong-token")
        guessed_token = verify_reset_token(user, guessed)
    except Exception as error:
        if str(error) == PATCH_ERROR:
            return CheckResult(False, False, PATCH_ERROR)
        return CheckResult(False, False, f"Проверка токена сломалась: {error}")

    availability_ok = bool(token) and correct_token is True and wrong_token is False
    security_ok = token != guessed and guessed_token is False

    if not availability_ok:
        return CheckResult(False, False, "Выданный токен не проходит обычную проверку.")
    if not security_ok:
        return CheckResult(True, False, "Токен всё ещё можно угадать по данным пользователя.")
    return CheckResult(True, True, "Патч принят: reset-token не угадывается.")
