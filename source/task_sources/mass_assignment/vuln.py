# Учебная функция обновления профиля.
def update_profile(user, data):
    changes = dict(data)
    user["last_action"] = "profile_update"

    ### НАЧАЛО БЛОКА РЕДАКТИРОВАНИЯ ###
    user.update(changes)
    return user
    ### КОНЕЦ БЛОКА РЕДАКТИРОВАНИЯ ###
