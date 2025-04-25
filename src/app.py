from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from shiny import reactive, ui, App
import uvicorn

import repository.timeseries_repository
import repository.user_repository
import view.auth_page
import view.datasource_page
import view.snapshot_page
import view.main_select_page
import view.snapshots_list_page
import view.datasources_list_page
import models.datasource
from api import get_api_routes


class AppStatus:
    current_page = reactive.value(("auth_page_ui", {}))
    snapshot_load_state = reactive.value(0)
    current_user = reactive.value(None)

    def get_current_page(self):
        return self.current_page.get()

    def open_snapshot_page(self, uuid):
        self.current_page.set(("snapshot_page_ui", {"uuid": uuid}))

    def open_datasource_page(self, datasource):
        self.current_page.set(
            ("datasource_page_ui", {"datasource": datasource}))

    def open_main_select_page(self):
        self.current_page.set(("main_select_page_ui", {}))

    def open_snapshots_list_page(self):
        self.current_page.set(("snapshots_list_page_ui", {}))

    def open_datasources_list_page(self):
        self.current_page.set(("datasources_list_page_ui", {}))


# The commented-out navbar_ui and page rendering functions are preserved but not formatted
# as they appear to be older versions of the code

def app_ui(request):
    return ui.page_fluid(
        ui.div(id="navbar_container"),
        ui.div(id="page_content")
    )


def app_server():
    user_repository = repository.user_repository.UserRepository()
    timeseries_repository = repository.timeseries_repository.TimeSeriesRepository()

    datasources = [
        models.datasource.CBR_datasource(timeseries_repository),
        models.datasource.Comtrade_datasource(timeseries_repository),
        models.datasource.Worldbank_datasource(timeseries_repository)
    ]

    app_status = AppStatus()

    def server_func(input, output, session):
        # register all server funcs
        @reactive.effect
        @reactive.event(app_status.current_page)
        def handle_page_change():
            page = app_status.get_current_page()

            ui.remove_ui("#navbar_container *", multiple=True)

            if page[0] == "auth_page_ui":
                ui.insert_ui(
                    ui.navset_bar(
                        ui.nav_spacer(),
                        title="Socio-economic indicators tool",
                        id="selected_navset_bar",
                    ),
                    "#navbar_container",
                )
            else:
                ui.insert_ui(
                    ui.navset_bar(
                        ui.nav_spacer(),
                        ui.nav_control(
                            ui.input_action_button(
                                "navbar_go_to_main_select_page", "Главная страница")
                        ),
                        ui.nav_control(
                            ui.input_action_button(
                                "navbar_go_to_datasources_list_page", "Список источников")
                        ),
                        ui.nav_control(
                            ui.input_action_button(
                                "navbar_go_to_snapshots_list_page", "Список слепков")
                        ),
                        title="Socio-economic indicators tool",
                        id="selected_navset_bar",
                    ),
                    "#navbar_container",
                )

            ui.remove_ui("#page_content *")

            print(page)

            if page[0] == "auth_page_ui":
                ui.insert_ui(view.auth_page.auth_page_ui(),
                             selector="#page_content")
                view.auth_page.auth_page_server(
                    user_repository, app_status)(input, output, session)
            elif page[0] == "datasource_page_ui":
                ui.insert_ui(
                    view.datasource_page.datasource_page_ui(
                        page[1]["datasource"]),
                    "#page_content"
                )
                view.datasource_page.datasource_page_server(
                    page[1]["datasource"],
                    timeseries_repository,
                    app_status
                )(input, output, session)
            elif page[0] == "snapshot_page_ui":
                ui.insert_ui(
                    view.snapshot_page.snapshot_page_ui(
                        timeseries_repository, page[1]['uuid']),
                    "#page_content"
                )
                view.snapshot_page.snapshot_page_server(
                    timeseries_repository,
                    page[1]['uuid']
                )(input, output, session)
            elif page[0] == "main_select_page_ui":
                ui.insert_ui(
                    view.main_select_page.main_select_page_ui(app_status),
                    "#page_content"
                )
                view.main_select_page.main_select_page_server(
                    app_status)(input, output, session)
            elif page[0] == "snapshots_list_page_ui":
                ui.insert_ui(
                    view.snapshots_list_page.snapshots_list_page_ui(), "#page_content")
                view.snapshots_list_page.snapshots_list_page_server(
                    timeseries_repository,
                    app_status
                )(input, output, session)
            elif page[0] == "datasources_list_page_ui":
                ui.insert_ui(
                    view.datasources_list_page.datasources_list_page_ui(
                        datasources, timeseries_repository),
                    "#page_content"
                )
                view.datasources_list_page.datasources_list_page_server(
                    datasources,
                    app_status
                )(input, output, session)

        @reactive.effect
        @reactive.event(input.navbar_go_to_datasources_list_page, ignore_init=True)
        def handle_navbar_go_to_datasources_list_page():
            app_status.open_datasources_list_page()

        @reactive.effect
        @reactive.event(input.navbar_go_to_snapshots_list_page, ignore_init=True)
        def handle_navbar_go_to_snapshots_list_page():
            app_status.open_snapshots_list_page()

        @reactive.effect
        @reactive.event(input.navbar_go_to_main_select_page, ignore_init=True)
        def handle_navbar_go_to_main_select_page():
            app_status.open_main_select_page()

    return server_func


shiny_app = App(app_ui, app_server())

routes = [
    Mount("/api", routes=get_api_routes()),
    Mount("/", shiny_app),
]

app = Starlette(routes=routes, debug=True)

print("Available routes:")
for route in app.routes:
    if isinstance(route, Mount):
        print(f"Mount: {route.path}")
        for subroute in route.routes:
            print(f"  - {subroute.path}")
    else:
        print(f"Route: {route.path}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
