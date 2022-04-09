# Этот код ничто нигде не сохраняет.
# Он лишь отправляет запрос яндексу на получение токена.
# Будьте аккуратны с ним и никому не показывайте!

# Измените эти переменные:
username = '' # Ваш логин или почта
password = '' # Ваш пароль

# Дальше код

import requests

link_post = "https://oauth.yandex.com/token"
header = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
}

try:
    request_post = f"grant_type=password&client_id=23cabbbdc6cd418abb4b39c32c41195d&client_secret=53bc75238f0c4d08a118e51fe9203300&username={username}&password={password}"
    request_auth = requests.post(link_post, data=request_post, headers=header)
    if request_auth.status_code == 200:
        json_data = request_auth.json()
        token = json_data.get('access_token')
        print(token)
    else:
        print('Не удалось получить токен')
except requests.exceptions.ConnectionError:
    print('Не удалось отправить запрос на получение токена')
