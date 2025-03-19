from shiny import reactive
from shiny.express import input, ui, render, module

import models.datasource
import repository.timeseries_repository

@module
def datasource_block_ui(input, output, session, datasource: models.datasource.Datasource, repository: repository.timeseries_repository.TimeSeriesRepository, app_status):
    @render.express
    def _():
        with ui.layout_columns(
            col_widths={"sm": (12)},
        ):
            with ui.card():
                ui.card_header(datasource.name)

                datasource.description

                with ui.layout_columns():
                    datasource_info = repository.get_datasource_info(datasource.uuid)

                    with ui.value_box():
                        "Дата сбора последнего слепка"
                        datasource_info['last_snapshot_timestamp'] if 'last_snapshot_timestamp' in datasource_info else '-'
                    with ui.value_box():
                        "Автор запуска последнего сбора слепка"
                        datasource_info['last_snapshot_author'] if 'last_snapshot_author' in datasource_info else '-'
                    with ui.value_box():
                        "Число сохраненных в базе слепков"
                        datasource_info['snapshots_count'] if 'snapshots_count' in datasource_info else 0

                ui.input_action_button("open_datasource", "Открыть страницу источника данных")

    @reactive.effect
    @reactive.event(input.open_datasource, ignore_init=True)
    def _():
        app_status.open_datasource_page(datasource)

@module
def datasources_list_page_ui(input, output, session, datasources: list[models.datasource.Datasource], repository, app_status):
    for datasource in datasources:
        datasource_block_ui(datasource.uuid.replace('-', '_'), datasource, repository, app_status)
