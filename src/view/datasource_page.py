from shiny import reactive, req
from shiny.express import input, ui, render, module

import models.datasource
import repository.timeseries_repository

@module
def datasource_page_ui(input, output, session, datasource: models.datasource.Datasource, repository: repository.timeseries_repository.TimeSeriesRepository, app_status):
    with ui.layout_columns(
        col_widths={"sm": (12, 6, 6)},
    ):
        with ui.card():
            ui.card_header(datasource.name)

            datasource.description

        with ui.card():
            ui.card_header("Создание запроса на выгрузку данных")

            datasource.snapshot_requester("snapshot_requester", repository, app_status.snapshot_load_state)

        with ui.card():
            ui.card_header("Список выгруженных snapshot'ов")

            @render.data_frame
            @reactive.event(app_status.snapshot_load_state)
            def datasource_snapshots():
                kwargs = {
                    'datasource_names': [datasource.name]
                }
                return render.DataGrid(repository.get_snapshots(**kwargs).sort_values(by='timestamp', ascending=False), selection_mode="row", width="100%")
            
            
            
            @reactive.effect
            @reactive.event(datasource_snapshots.cell_selection, ignore_init=True)
            def _():
                data_selected = datasource_snapshots.data_view(selected=True)
                req(not data_selected.empty)

                uuid = data_selected['uuid'].values[0]
                print(f'Selected uuid: {uuid}')
                app_status.open_snapshot_page(uuid)