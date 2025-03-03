
# repository

from dataclasses import dataclass
import pandas as pd

@dataclass
class DataSource:
    pass

@dataclass
class Snapshot:
    pass

@dataclass
class TimeSeries:
    pass



import psycopg2

def hash_password(password: str) -> str:
    return password

class UsersRepository:
    def __init__(self):
        try:
            self.connection = psycopg2.connect("host=localhost port=5432 dbname=socio_economic_indicators_tool user=postgres")
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
            cursor = self.connection.cursor()
            cursor.execute("select count(*) as count from socio_economic_indicators_tool.users where login=%s and password_hash=%s", [login, hash_password(password)])
            
            check_result = cursor.fetchone()[0] == 1
            cursor.close()
            return check_result

        except psycopg2.OperationalError as exc:
            print(exc)


# timeseries repo

import clickhouse_connect

class TimeSeriesRepository:
    def __init__(self):
        try:
            self.client = clickhouse_connect.get_client(host='localhost', username='default', database='socio_economic_indicators_tool')
        except Exception as exc:
            print(exc)

    def get_snapshots(self, datasource_names=None, lower_timestamp=None, upper_timestamp=None, limit=10):
        try:
            datasource_names_str = ', '.join(f"'{name}'" for name in datasource_names)

            query = f"""
            SELECT s.uuid, s.timestamp, d.name
            FROM Snapshot s
            JOIN DataSource d ON s.datasource_uuid = d.uuid
            WHERE 1=1
            {(f"AND d.name IN ({datasource_names_str})" if datasource_names else "")}
            {(f"AND s.timestamp >= '{lower_timestamp}'" if lower_timestamp else "")}
            {(f"AND s.timestamp <= '{upper_timestamp}'" if upper_timestamp else "")}
            LIMIT {limit}"""

            print(query)

            result = self.client.query(query)
            print('DEBUG: get_snapshots')
            return pd.DataFrame(data=result.result_rows, columns=result.column_names) 
            # [{
            #     'uuid': row[0],
            #     'timestamp': row[1],
            #     'datasource_name': row[2]
            # } for row in result.result_rows]
        except Exception as exc:
            print('exc')
            print(exc)

    def get_snapshot_timestamp_boundaries(self):
        try:
            query = f"""
            SELECT MIN(s.timestamp) as min_timestamp, MAX(s.timestamp) as max_timestamp
            FROM socio_economic_indicators_tool.Snapshot s
            """

            result = self.client.query(query)
            if result:
                min_timestamp = result.result_rows[0][0]
                max_timestamp = result.result_rows[0][1]
                return min_timestamp, max_timestamp

            print('DEBUG: get_snapshot_timestamp_boundaries')
            return None, None
        except Exception as exc:
            print('exc')
            print(exc)

    def get_datasource_distinct_names(self):
        try:
            query = f"""
            SELECT DISTINCT d.name
            FROM socio_economic_indicators_tool.DataSource d
            """

            result = self.client.query(query)
            print('DEBUG: get_datasource_distinct_names')
            return [row[0] for row in result.result_rows]
        except Exception as exc:
            print('exc')
            print(exc)


    def __del__(self):
        pass


# TimeSeriesRepository()

#view

from shiny import reactive
from shiny.express import input, ui, render, module

repository = UsersRepository()

repository2 = TimeSeriesRepository()

auth_success = reactive.value(False)

current_page = reactive.value()


ui.page_opts(
    title="Socio-economic indicators tool"
)

# @render.ui
# def app():
#     if auth_success.get():
#         return
#         with ui.sidebar():
            
#     else:
#         return [
#             ui.input_text("login_input", "Login"),
#             ui.input_password("password_input", "Password"),
#             ui.input_action_button("send_auth_data_button", "Authorize")
#         ]

# data sources



# snapshots

# min_timestamp, max_timestamp = repository2.get_snapshot_timestamp_boundaries()

# with ui.sidebar():
#     ui.input_date_range("snapshots_daterange", "Date range", min=min_timestamp, max=max_timestamp, start=min_timestamp, end=max_timestamp)

#     datasource_names = repository2.get_datasource_distinct_names()
#     ui.input_selectize("snapshots_datasource_select", "Datasource", choices=datasource_names, multiple=True)

#     ui.input_action_button("snapshots_reset_filters", "Reset filter")

# with ui.card(full_screen=True):
#     ui.card_header("Snapshots list")

#     @render.data_frame
#     @reactive.event(input.snapshots_datasource_select, input.snapshots_daterange)
#     def table():
#         kwargs = {
#             'datasource_names': input.snapshots_datasource_select(),
#             'lower_timestamp': input.snapshots_daterange()[0],
#             'upper_timestamp': input.snapshots_daterange()[1],
#         }

#         print(kwargs)
#         return render.DataGrid(repository2.get_snapshots(**kwargs), selection_mode="row", width="100%")

# @reactive.effect
# @reactive.event(input.snapshots_reset_filters)
# def _():
#     ui.update_select('snapshots_datasource_select', selected=[])
    
#     ui.update_date_range('snapshots_daterange', start=min_timestamp, end=max_timestamp)



@reactive.effect
@reactive.event(input.send_auth_data_button)
def send_auth_request():
    login = input.login_input()
    password = input.password_input()

    auth_success.set(repository.check_credentials(login, password))