from shiny import reactive, ui

import models.datasource
import repository.timeseries_repository


def datasources_list_page_ui(
    datasources: list[models.datasource.Datasource],
    repository: repository.timeseries_repository.TimeSeriesRepository
):
    blocks = []
    for datasource in datasources:
        datasource_info = repository.get_datasource_info(datasource.uuid)

        block = ui.layout_columns(
            ui.card(
                ui.card_header(datasource.name),
                ui.p(datasource.description),
                ui.layout_columns(
                    ui.value_box(
                        "Дата сбора последнего слепка",
                        datasource_info.get('last_snapshot_timestamp', '-'),
                    ),
                    ui.value_box(
                        "Автор запуска последнего сбора слепка",
                        datasource_info.get('last_snapshot_author', '-'),
                    ),
                    ui.value_box(
                        "Число сохраненных в базе слепков",
                        datasource_info.get('snapshots_count', 0),
                    ),
                ),
                ui.input_action_button(
                    f"open_datasource_{datasource.get_ui_id()}",
                    "Открыть страницу источника данных"
                )
            ),
            col_widths={"sm": (12)},
        )
        blocks.append(block)

    return ui.div(*blocks)


def datasources_list_page_server(
    datasources: list[models.datasource.Datasource],
    app_status
):
    def server_func(input, output, session):
        for datasource in datasources:
            button_id = f"open_datasource_{datasource.get_ui_id()}"

            @reactive.effect
            @reactive.event(
                lambda ds=datasource, bid=button_id: getattr(input, bid)(),
                ignore_init=True
            )
            def handle_open_datasource(ds=datasource):
                print(f"Открываем источник данных: {ds.name}")
                app_status.open_datasource_page(ds)

    return server_func
