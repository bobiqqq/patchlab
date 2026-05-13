import secrets


# Учебные функции выпуска и проверки reset-token.
### НАЧАЛО БЛОКА РЕДАКТИРОВАНИЯ ###
def make_reset_token(user):
    token = str(user.get("id")) + "-" + user.get("username", "")
    user["reset_token"] = token
    return token


def verify_reset_token(user, token):
    return token == user.get("reset_token")
### КОНЕЦ БЛОКА РЕДАКТИРОВАНИЯ ###
