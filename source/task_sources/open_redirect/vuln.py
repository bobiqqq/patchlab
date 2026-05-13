# Учебная функция проверки redirect URL.
def is_safe_redirect(url):
    url = (url or "").strip()
    default_url = "/dashboard"
    target = url or default_url

    ### НАЧАЛО БЛОКА РЕДАКТИРОВАНИЯ ###
    return bool(target)
    ### КОНЕЦ БЛОКА РЕДАКТИРОВАНИЯ ###
