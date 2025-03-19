import psycopg2

from shiny import ui
import traceback

class UserRepository:
    def __init__(self):
        try:
            self.connection = psycopg2.connect("host=localhost port=5432 dbname=socio_economic_indicators_tool user=postgres")
        except psycopg2.OperationalError as exc:
            ui.notification_show(f"Failed to establish connection to database: {exc}", type="error")
            traceback.format_exc()

    def __del__(self):
        try:
            if (self.connection is not None):
                self.connection.close()
        except psycopg2.OperationalError as exc:
            traceback.format_exc()

    def check_credentials(self, login, password) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute("select count(*) as count from socio_economic_indicators_tool.users where login=%s and password_hash=crypt(%s, password_hash)", [login, password])
            
            check_result = cursor.fetchone()[0] == 1
            cursor.close()
            return check_result
        except psycopg2.OperationalError as exc:
            ui.notification_show(f"Failed to check credentials: {exc}", type="error")
            traceback.format_exc()