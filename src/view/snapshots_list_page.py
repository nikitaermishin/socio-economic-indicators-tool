from shiny import reactive, req
from shiny.express import input, ui, render, module

import repository.timeseries_repository

@module
def snapshots_list_page_ui(input, output, session, repository: repository.timeseries_repository.TimeSeriesRepository, app_status):
    snapshots = repository.get_snapshots()

    with ui.layout_columns(
        col_widths={"sm": (12)},
    ):

        with ui.card():
            ui.card_header('Список слепков данных')

            @render.data_frame
            def snapshots_list():
                return render.DataGrid(snapshots.sort_values(by='timestamp', ascending=False), selection_mode="row", width="100%", filters=True)
                
    @reactive.effect
    @reactive.event(snapshots_list.cell_selection, ignore_init=True)
    def _():
        data_selected = snapshots_list.data_view(selected=True)
        req(not data_selected.empty)

        uuid = data_selected['uuid'].values[0]
        print(f'Selected uuid: {uuid}')
        app_status.open_snapshot_page(uuid)