import sqlite3

def login(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # УЯЗВИМО: строковая подстановка позволяет провести SQL-инъекцию
    # Пример атаки: admin' --
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    cursor.execute(query, (username, password,))
    user = cursor.fetchone()
    conn.close()
    return user
