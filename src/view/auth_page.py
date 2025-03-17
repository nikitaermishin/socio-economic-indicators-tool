from shiny import reactive
from shiny.express import input, ui, render, module

import repository.user_repository

@module
def auth_page_ui(input, output, session, repository: repository.user_repository.UserRepository, app_status):
    @render.express
    def _():
        with ui.layout_columns(
            col_widths={"sm": (6, 6)},
        ):
            if app_status.get_current_page()[0] != 'auth_page_ui':
                return

            with ui.card():
                ui.card_header("Authorization")

                ui.input_text("login_input", "Login"),
                ui.input_password("password_input", "Password"),
                ui.input_action_button("send_auth_data_button", "Authorize")

            with ui.card():
                ui.card_header("Description")

                """
                In the current conditions of the Russian economy and global challenges, the information availability of socio-economic statistics is becoming increasingly limited. Sanctions pressure from international partners and governments has led to the fact that many data sources are becoming inaccessible, censored, or their contents are being modified. This necessitates the preservation of data snapshots and archives of indicators, both for retrospective analysis and for future use, especially if access to data continues to be limited.
                """

    @reactive.effect
    @reactive.event(input.send_auth_data_button, ignore_init=True)
    def _():
        login = input.login_input()
        password = input.password_input()

        if (repository.check_credentials(login, password)):
            app_status.open_main_select_page()
