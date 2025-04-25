from shiny import reactive, req, ui, render

import repository.timeseries_repository


def snapshots_list_page_ui():
    return ui.layout_columns(
        ui.card(
            ui.card_header('Список слепков данных'),
            ui.output_data_frame("snapshots_list"),
        ),
        col_widths={"sm": (12)},
    )


def snapshots_list_page_server(
    repository: repository.timeseries_repository.TimeSeriesRepository,
    app_status
):
    snapshots = repository.get_snapshots()

    def server_func(input, output, session):
        @render.data_frame
        def snapshots_list():
            return render.DataGrid(
                snapshots.sort_values(by='timestamp', ascending=False),
                selection_mode="row",
                width="100%",
                filters=True
            )

        @reactive.effect
        @reactive.event(snapshots_list.cell_selection, ignore_init=True)
        def handle_selection():
            data_selected = snapshots_list.data_view(selected=True)
            req(not data_selected.empty)

            uuid = data_selected['uuid'].values[0]
            print(f'Selected uuid: {uuid}')
            app_status.open_snapshot_page(uuid)

    return server_func
