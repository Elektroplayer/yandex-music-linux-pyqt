from PyQt5 import QtWidgets
import requests

from windows.models.LoginDialogModel import Ui_Dialog


class LoginDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.loginbutton.clicked.connect(self.login)

    def login(self):
        login = self.loginInput.text()
        password = self.passinput.text()

        if len(login) == 0 or len(password) == 0:
            self.label.setText('Поля не должны быть пустыми!')
            return

        link_post = "https://oauth.yandex.com/token"
        header = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        }

        try:
            request_post = f"grant_type=password&client_id=23cabbbdc6cd418abb4b39c32c41195d&client_secret=53bc75238f0c4d08a118e51fe9203300&username={login}&password={password}"
            request_auth = requests.post(link_post, data=request_post, headers=header)
            if request_auth.status_code == 200:
                json_data = request_auth.json()
                self.token = json_data.get('access_token')

                if self.token != '':
                    self.close()
                else:
                    self.label.setText('Произошла ошибка, попробуйте снова')
            else:
                self.label.setText('Не верный логин или пароль')
        except requests.exceptions.ConnectionError:
            self.label.setText('Не удалось отправить запрос')
