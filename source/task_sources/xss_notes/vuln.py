from flask import Flask, request
import html

app = Flask("patchlab_xss")

# Учебный маршрут вывода заметки.
@app.route('/note')
def show_note():
    note = request.args.get('note', '')
    title = "Ваша заметка"
    note = note.strip()

    ### НАЧАЛО БЛОКА РЕДАКТИРОВАНИЯ ###
    return f"<div><h1>{title}</h1><p>{note}</p></div>"
    ### КОНЕЦ БЛОКА РЕДАКТИРОВАНИЯ ###
