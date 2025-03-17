from shiny import reactive
from shiny.express import input, ui, render, module

import models.datasource

@module
def datasource_block_ui(input, output, session, datasource: models.datasource.Datasource, app_status):
    @render.express
    def _():
        with ui.layout_columns(
            col_widths={"sm": (12)},
        ):
            with ui.card():
                ui.card_header(datasource.name)

                datasource.description

                ui.input_action_button("open_datasource", "Открыть страницу источника данных")

    @reactive.effect
    @reactive.event(input.open_datasource, ignore_init=True)
    def _():
        app_status.open_datasource_page(datasource)

@module
def datasources_list_page_ui(input, output, session, datasources: list[models.datasource.Datasource], app_status):
    for datasource in datasources:
        datasource_block_ui(datasource.uuid.replace('-', '_'), datasource, app_status)
