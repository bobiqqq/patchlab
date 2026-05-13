# Учебная функция проверки доступа к админ-панели.
def can_open_admin_panel(user):
    username = user.get("username", "")
    role = user.get("role", "guest")
    account_enabled = user.get("enabled", True)

    ### НАЧАЛО БЛОКА РЕДАКТИРОВАНИЯ ###
    is_allowed = role == "admin" or username == "admin"
    return account_enabled and is_allowed
    ### КОНЕЦ БЛОКА РЕДАКТИРОВАНИЯ ###
