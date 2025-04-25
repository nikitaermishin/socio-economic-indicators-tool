from shiny import reactive, ui


def main_select_page_ui(app_status):
    return ui.layout_columns(
        ui.card(
            ui.p(
                f"Текущий авторизованный пользователь: {app_status.current_user.get()}"),
        ),
        ui.card(
            ui.input_action_button(
                "go_to_datasources_list_page", "Перейти к списку источников данных"),
        ),
        ui.card(
            ui.input_action_button(
                "go_to_snapshots_list_page", "Перейти к списку слепков данных"),
        ),
        col_widths={"sm": (12, 6, 6)},
    )


def main_select_page_server(app_status):
    def server_func(input, output, session):
        @reactive.effect
        @reactive.event(input.go_to_datasources_list_page, ignore_init=True)
        def handle_go_to_datasources():
            app_status.open_datasources_list_page()

        @reactive.effect
        @reactive.event(input.go_to_snapshots_list_page, ignore_init=True)
        def handle_go_to_snapshots():
            app_status.open_snapshots_list_page()

    return server_func
