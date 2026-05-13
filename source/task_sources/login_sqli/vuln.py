import sqlite3

# Учебная функция входа пользователя.
def login(username, password):
    username = username.strip()
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    ### НАЧАЛО БЛОКА РЕДАКТИРОВАНИЯ ###
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    ### КОНЕЦ БЛОКА РЕДАКТИРОВАНИЯ ###
    user = cursor.fetchone()
    conn.close()
    return user
