
# repository

import psycopg2

def hash_password(password: str) -> str:
    return password

class Repository:
    def __init__(self):
        try:
            self.connection = psycopg2.connect("host=localhost port=5432 dbname=socio_economic_indicators_tool user=server password=meow")
            print("sun is up")
        except psycopg2.OperationalError as exc:
            print(exc)

    def __del__(self):
        try:
            # Оно none если упал нахуй конструктор
            if (self.connection is not None):
                self.connection.close()
            print("sun is down")
        except psycopg2.OperationalError as exc:
            print(exc)

    def check_credentials(self, login, password) -> bool:
        try:
            print("TODO WOW")
            cursor = self.connection.cursor()
            cursor.execute("select count(*) from pg_database.users where login=%s and passwordHash=%s" % (login, hash_password(password)))
            
            check_result = cursor.fetchone() == 1

            cursor.close()

            print(check_result)

            return check_result

        except psycopg2.OperationalError as exc:
            print(exc)


#view

from shiny import reactive
from shiny.express import input, ui

repository = Repository()

auth_success = reactive.value(False)

ui.input_text("login_input", "Login")  
ui.input_password("password_input", "Password")
ui.input_action_button("send_auth_data_button", "Authorize")

@reactive.effect
@reactive.event(input.send_auth_data_button)
def send_auth_request():
    login = input.login_input()
    password = input.password_input()

    print("Sending auth request")
    repository.check_credentials(login, password)