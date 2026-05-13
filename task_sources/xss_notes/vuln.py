from flask import Flask, request
import html

app = Flask("patchlab_xss")

@app.route('/note')
def show_note():
    # Учебный маршрут вывода заметки.
    note = request.args.get('note', '')
    ### БЛОК РЕДАКТИРОВАНИЯ ###
    # УЯЗВИМО: пользовательский ввод выводится без экранирования
    # Пример атаки: <script>alert(1)</script>
    return f"<div><h1>Ваша заметка</h1><p>{note}</p></div>"
    ### БЛОК РЕДАКТИРОВАНИЯ ###
