from shiny import reactive, req, ui, render

import models.datasource
import repository.timeseries_repository


def datasource_page_ui(
    datasource: models.datasource.Datasource
):
    return ui.layout_columns(
        ui.card(
            ui.card_header(datasource.name),
            ui.p(datasource.description),
        ),
        ui.card(
            ui.card_header("Создание запроса на выгрузку данных"),
            ui.div(id="snapshot_requester_container")
        ),
        ui.card(
            ui.card_header("Список выгруженных snapshot'ов"),
            ui.output_data_frame("datasource_snapshots")
        ),
        col_widths={"sm": (12, 6, 6)}
    )


def datasource_page_server(
    datasource: models.datasource.Datasource,
    repository: repository.timeseries_repository.TimeSeriesRepository,
    app_status
):
    def server_func(input, output, session):
        ui.insert_ui(
            datasource.snapshot_requester_ui(),
            selector="#snapshot_requester_container"
        )

        datasource.snapshot_requester_server(
            repository,
            app_status.snapshot_load_state,
            app_status.current_user.get()
        )(input, output, session)

        @render.data_frame
        @reactive.event(app_status.snapshot_load_state)
        def datasource_snapshots():
            kwargs = {
                'datasource_names': [datasource.name]
            }
            snapshots = repository.get_snapshots(**kwargs)
            df = (
                snapshots.sort_values(by='timestamp', ascending=False)
                if 'timestamp' in snapshots else snapshots
            )
            return render.DataGrid(
                df,
                selection_mode="row",
                width="100%",
                filters=True
            )

        @reactive.effect
        @reactive.event(datasource_snapshots.cell_selection, ignore_init=True)
        def handle_snapshot_selection():
            data_selected = datasource_snapshots.data_view(selected=True)
            req(not data_selected.empty)

            uuid = data_selected['uuid'].values[0]
            print(f'Selected uuid: {uuid}')
            app_status.open_snapshot_page(uuid)

    return server_func
