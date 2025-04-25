from shiny import reactive, ui, render

import matplotlib.pyplot as plt
import pandas as pd


def snapshot_page_ui(repository, snapshot_uuid):
    snapshot = repository.get_snapshot_by_uuid(snapshot_uuid)

    return ui.layout_columns(
        ui.value_box(
            "Дата сбора слепка",
            str(snapshot.timestamp) if snapshot.timestamp else '-'
        ),
        ui.value_box(
            "Автор слепка",
            snapshot.author if snapshot.author else '-'
        ),
        ui.card(
            ui.navset_card_tab(
                ui.nav_panel(
                    "Таблица",
                    ui.output_data_frame("table")
                ),
                ui.nav_panel(
                    "График",
                    ui.output_plot("plot")
                ),
                id="selected_navset_card_tab"
            )
        ),
        ui.card(
            ui.card_header('Локальная загрузка данных'),
            ui.download_button("csv_download", "Download CSV"),
            ui.download_button("json_download", "Download JSON"),
        ),
        ui.card(
            ui.card_header('Загрузка данных по API'),
            ui.p(
                'Для использования данных по API в своем коде воспользуйтесь запросом ниже:'),
            ui.code('import requests'),
            ui.code(
                f"response = requests.get('http://127.0.0.1:80/api/snapshot/get-by-uuid/{snapshot_uuid}')"),
            ui.code('data = response.json()')
        ),
        col_widths={"sm": (6, 6, 12, 6, 6)},
    )


def snapshot_page_server(repository, snapshot_uuid):
    snapshot = repository.get_snapshot_by_uuid(snapshot_uuid)
    dataframe = snapshot.to_dataframe().reset_index()

    def server_func(input, output, session):
        @render.data_frame
        def table():
            return render.DataGrid(dataframe, selection_mode="row", width="100%")

        @render.plot()
        def plot():
            fig, ax = plt.subplots()
            fig.subplots_adjust(right=0.6)

            df = dataframe.copy()
            df.index = pd.to_datetime(df['index'], errors='coerce')
            print('DEBUG', len(df.index))

            if getattr(df.index, "tz", None) is not None:
                df.index = df.index.tz_convert(None)

            df_resampled = df.resample('ME').mean()
            print('DEBUG', len(df_resampled.index))
            df_resampled = df_resampled.drop(columns=['index'])

            print('DEBUG', len(df_resampled.columns))

            for column in df_resampled.columns:
                print('DEBUG', df_resampled[column], column)
                ax.plot(
                    df_resampled.index,
                    df_resampled[column],
                    label=column,
                    marker='.'
                )

            ax.set_xlabel('Index')
            ax.set_ylabel('Values')
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=6)
            plt.tight_layout()
            ax.grid(True)

            return fig

        @render.download(filename="snapshot.csv")
        def csv_download():
            yield dataframe.to_csv()

        @render.download(filename="snapshot.json")
        def json_download():
            yield dataframe.to_json()

    return server_func
