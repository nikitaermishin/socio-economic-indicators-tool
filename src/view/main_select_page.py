from shiny import reactive
from shiny.express import input, ui, render, module

@module
def main_select_page_ui(input, output, session, app_status):
    @render.express
    def _():
        with ui.layout_columns(
            col_widths={"sm": (12, 6, 6)},
        ):
            with ui.card():
                f"Текущий авторизованный пользователь: {app_status.current_user.get()}"
            with ui.card():
                ui.input_action_button("go_to_datasources_list_page", "Перейте к списку источников данных")

            with ui.card():
                ui.input_action_button("go_to_snapshots_list_page", "Перейти к списку слепков данных")

    @reactive.effect
    @reactive.event(input.go_to_datasources_list_page, ignore_init=True)
    def _():
        app_status.open_datasources_list_page()

    @reactive.effect
    @reactive.event(input.go_to_snapshots_list_page, ignore_init=True)
    def _():
        app_status.open_snapshots_list_page()
