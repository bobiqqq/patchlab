# Учебная функция чтения страниц из хранилища.
def read_page(filename, storage):
    filename = (filename or "").strip()
    base_dir = "pages/"

    ### НАЧАЛО БЛОКА РЕДАКТИРОВАНИЯ ###
    path = base_dir + filename
    if path not in storage:
        path = filename
    return storage.get(path)
    ### КОНЕЦ БЛОКА РЕДАКТИРОВАНИЯ ###
