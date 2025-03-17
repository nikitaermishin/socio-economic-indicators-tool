from shiny import reactive
from shiny.express import input, ui, render, module

import repository.timeseries_repository
import repository.user_repository
import view.auth_page
import view.datasource_page
import view.snapshot_page
import view.main_select_page
import view.snapshots_list_page
import view.datasources_list_page
import models.datasource


class AppStatus:
    current_page = reactive.value(("auth_page_ui", {}))
    snapshot_load_state = reactive.value(0)

    def get_current_page(self):
        return self.current_page.get()
    
    def open_snapshot_page(self, uuid):
        self.current_page.set(("snapshot_page_ui", {"uuid": uuid}))

    def open_datasource_page(self, datasource):
        self.current_page.set(("datasource_page_ui", {"datasource": datasource}))

    def open_main_select_page(self):
        self.current_page.set(("main_select_page_ui", {}))

    def open_snapshots_list_page(self):
        self.current_page.set(("snapshots_list_page_ui", {}))

    def open_datasources_list_page(self):
        self.current_page.set(("datasources_list_page_ui", {}))

app_status = AppStatus()

@module
# @reactive.effect

def navbar_ui(input, output, session, app_status):
    @render.express
    @reactive.event(app_status.current_page)
    def _():
        with reactive.isolate():
            with ui.navset_bar(
                title="Socio-economic indicators tool",
                id="selected_navset_bar",
            ):
                page = app_status.get_current_page()

                if page[0] == "auth_page_ui":
                    return 

                ui.nav_spacer()
                with ui.nav_control():
                    ui.input_action_button("navbar_go_to_datasources_list_page", "Список источников")

                with ui.nav_control():
                    ui.input_action_button("navbar_go_to_snapshots_list_page", "Список слепков")

            @reactive.effect
            @reactive.event(input.navbar_go_to_datasources_list_page, ignore_init=True)
            def _():
                app_status.open_datasources_list_page()

            @reactive.effect
            @reactive.event(input.navbar_go_to_snapshots_list_page, ignore_init=True)
            def _():
                app_status.open_snapshots_list_page()

user_repository = repository.user_repository.UserRepository()
timeseries_repository = repository.timeseries_repository.TimeSeriesRepository()

datasources = [models.datasource.CBR_datasource(timeseries_repository), models.datasource.Comtrade_datasource, models.datasource.Worldbank_datasource]


navbar_ui("navbar_ui", app_status)

@render.express
@reactive.event(app_status.current_page)
def _():
    with reactive.isolate():
        page = app_status.get_current_page()

        if page[0] == "auth_page_ui":
            view.auth_page.auth_page_ui("auth_page_ui", user_repository, app_status)
        elif page[0] == "datasource_page_ui":
            view.datasource_page.datasource_page_ui("datasource_page_ui", page[1]["datasource"], timeseries_repository, app_status)
        elif page[0] == "snapshot_page_ui":
            view.snapshot_page.snapshot_page_ui("snapshot_page_ui", timeseries_repository, page[1]['uuid'])
        elif page[0] == "main_select_page_ui":
            view.main_select_page.main_select_page_ui("main_select_page_ui", app_status)
        elif page[0] == "snapshots_list_page_ui":
            view.snapshots_list_page.snapshots_list_page_ui("snapshots_list_page_ui", timeseries_repository, app_status)
        elif page[0] == "datasources_list_page_ui":
            view.datasources_list_page.datasources_list_page_ui("datasources_list_page_ui", datasources, app_status)

