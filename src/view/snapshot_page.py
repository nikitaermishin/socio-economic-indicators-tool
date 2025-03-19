from shiny import reactive, req
from shiny.express import input, ui, render, module

import matplotlib.pyplot as plt
import pandas as pd


@module
def snapshot_page_ui(input, output, session, repository, snapshot_uuid):
    snapshot = repository.get_snapshot_by_uuid(snapshot_uuid)
    dataframe = snapshot.to_dataframe().reset_index()

    with ui.layout_columns():
        with ui.value_box():
            "Дата сбора слепка"
            str(snapshot.timestamp) if snapshot.timestamp else '-'
        with ui.value_box():
            "Автор слепка"
            snapshot.author if snapshot.author else '-'


    with ui.layout_columns(
        col_widths={"sm": (12, 12)},
    ):

        with ui.card():
            ui.card_header('Слепок данных')

            with ui.navset_card_tab(id="selected_navset_card_tab"):
                with ui.nav_panel("Таблица"):
                    @render.data_frame
                    def table():
                        return render.DataGrid(dataframe, selection_mode="row", width="100%")

                with ui.nav_panel("График"):
                    @render.plot()
                    def plot():
                        fig, ax = plt.subplots()
                        df = dataframe.copy()
                        df.index = pd.to_datetime(df['index'], errors='coerce')
                        print('DEBUG', len(df.index))
                        df_resampled = df.resample('ME').mean()
                        print('DEBUG', len(df_resampled.index))
                        df_resampled = df_resampled.drop(columns=['index'])

                        print('DEBUG', len(df_resampled.columns))

                        for column in df_resampled.columns:
                            ax.plot(df_resampled.index, df_resampled[column], label=column)

                        ax.set_xlabel('Index')
                        ax.set_ylabel('Values')
                        ax.legend()
                        ax.grid(True)

                        return fig

        with ui.card():
            ui.card_header('Локальная загрузка данных')

            @render.download(label="Download CSV", filename="snapshot.csv")
            def csv_download():
                yield dataframe.to_csv()
            
            @render.download(label="Download JSON", filename="snapshot.json")
            def json_download():
                yield dataframe.to_json()
