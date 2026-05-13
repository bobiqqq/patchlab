import sqlite3

def login(username, password):
    # Учебная функция входа пользователя.
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    ### БЛОК РЕДАКТИРОВАНИЯ ###
    # УЯЗВИМО: строковая подстановка позволяет провести SQL-инъекцию
    # Пример атаки: admin' --
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    ### БЛОК РЕДАКТИРОВАНИЯ ###
    user = cursor.fetchone()
    conn.close()
    return user
