from shiny import reactive, ui

import repository.user_repository


def auth_page_ui():
    return ui.layout_columns(
        ui.card(
            ui.card_header("Authorization"),
            ui.input_text("login_input", "Login"),
            ui.input_password("password_input", "Password"),
            ui.input_action_button("send_auth_data_button", "Authorize")
        ),
        ui.card(
            ui.card_header("Description"),
            ui.p("""
            In the current conditions of the Russian economy and global challenges, 
            the information availability of socio-economic statistics is becoming increasingly limited. 
            Sanctions pressure from international partners and governments has led to the fact 
            that many data sources are becoming inaccessible, censored, or their contents are being modified. 
            This necessitates the preservation of data snapshots and archives of indicators, 
            both for retrospective analysis and for future use, 
            especially if access to data continues to be limited.
            """)
        ),
        col_widths={"sm": (6, 6)},
    )


def auth_page_server(
    repository: repository.user_repository.UserRepository,
    app_status
):
    def server(input, output, session):
        @reactive.effect
        @reactive.event(input.send_auth_data_button, ignore_init=True)
        def handle_auth():
            login = input.login_input()
            password = input.password_input()

            if repository.check_credentials(login, password):
                app_status.current_user.set(login)
                app_status.open_main_select_page()
            else:
                ui.notification_show("Invalid login or password", type="error")

    return server
