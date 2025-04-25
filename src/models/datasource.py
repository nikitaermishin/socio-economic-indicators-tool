from uuid import UUID
import requests
import json
import datetime
import traceback
import pycountry

import pandas as pd
from shiny import reactive, ui
import comtradeapicall

import models.snapshot
import models.timeseries


def ordered_dict_to_string(d):
    """
    Преобразует словарь в строку, где:
    1. Ключи упорядочены
    2. Пары ключ-значение соединены через двоеточие (:)
    3. Пары разделены запятыми (,)
    """
    # Сортируем ключи
    ordered_keys = sorted(d.keys())

    # Формируем список пар ключ:значение
    pairs = [f"{key}:{d[key]}" for key in ordered_keys]

    # Объединяем пары через запятую
    return ",".join(pairs)


class Datasource:
    name: str
    uuid: str
    description: str

    def __init__(self, repository):
        UUID(self.uuid, version=4)
        repository.try_insert_datasource(
            self.uuid, self.name, self.description)

    def snapshot_requester_ui(self):
        pass

    def snapshot_requester_server(self, repository, snapshot_load_state, author):
        pass

    def get_ui_id(self):
        return f"datasource_{self.uuid.replace("-", "_")}"


class CBR_datasource(Datasource):
    name = "Сервис получения данных Банка России"
    uuid = "e18295ec-fee5-4793-8065-b270d9934acf"
    description = """
    Сервис получения данных предназначен для просмотра, визуализации, сравнения и автоматического получения через API данных статистических показателей публикаций официальной статистической информации.\n\n

    В интерфейсе сервиса выберите категорию, показатель и/или разрез, задайте длину временного ряда в поле «Годы». Временной ряд показателя отображается в табличном или графическом виде.
    Показатель может не иметь разреза, в таком случае поле «Разрез» будет не доступно для выбора.
    """

    base_url = "https://cbr.ru/dataservice"

    def __init__(self, repository):
        super().__init__(repository)

    def get_data(self, kwargs, author):
        """
        Достаем данные по API ЦБ РФ
        Дока https://cbr.ru/statistics/data-service/APIdocumentation/
        """
        def build_request(kwargs):
            return self.base_url + "/data?" + "&".join([f"{key}={value}" for key, value in kwargs.items()])

        response = requests.get(build_request(kwargs))
        response.raise_for_status()

        print(response.text)
        snapshot = self.to_snapshot(json.loads(response.text), author)

        print('\n\n\n\n\n')
        print(snapshot.serialize())
        return snapshot

    def get_publication_names(self):
        """
        Достаем список публикаций
        """
        def build_request():
            return self.base_url + f"/publications"

        try:
            response = requests.get(build_request())
            response.raise_for_status()

            print(response.text)
            if response.text is not None:
                return json.loads(response.text)
            else:
                return []
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP ошибка: {http_err}')
        except Exception as err:
            print(traceback.format_exc())

    def get_dataset_names(self, publication_id):
        def build_request(publication_id):
            return self.base_url + f"/datasets?publicationId={publication_id}"

        try:
            response = requests.get(build_request(publication_id))
            response.raise_for_status()

            print(response.text)
            if response.text is not None:
                return json.loads(response.text)
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP ошибка: {http_err}')
        except Exception as err:
            print(traceback.format_exc())

        return []

    def get_measure_names(self, dataset_id):
        def build_request(dataset_id):
            return self.base_url + f"/measures?datasetId={dataset_id}"

        try:
            response = requests.get(build_request(dataset_id))
            response.raise_for_status()

            print(response.text)
            if response.text is not None:
                return json.loads(response.text)
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP ошибка: {http_err}')
        except Exception as err:
            print(traceback.format_exc())

        return []

    def get_years_range(self, dataset_id, measure_id):
        def build_request(dataset_id, measure_id):
            return self.base_url + f"/years?datasetId={dataset_id}&measureId={measure_id}"

        try:
            response = requests.get(build_request(dataset_id, measure_id))
            response.raise_for_status()

            print(response.text)
            return json.loads(response.text)
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP ошибка: {http_err}')
        except Exception as err:
            print(traceback.format_exc())

    def to_snapshot(self, json_, author):
        assert len(json_['SType']) == 1

        timeseries_values: dict[int, models.timeseries.TimeseriesValue] = {}
        for data_elem in json_['RawData']:
            elem_id = data_elem['element_id']
            if elem_id not in timeseries_values.keys():
                timeseries_values[elem_id] = []
            timeseries_values[elem_id].append(
                models.timeseries.TimeseriesValue(
                    timestamp=datetime.datetime.fromisoformat(
                        data_elem['date']).date(),
                    value=data_elem['obs_val']
                )
            )

        snapshot_name = json_['SType'][0]['dsName'] + \
            ' - ' + json_['SType'][0]['PublName']
        timeseries: list[models.timeseries.Timeseries] = []
        for header in json_['headerData']:
            name = header['elname']

            timeseries.append(
                models.timeseries.Timeseries(
                    name=name,
                    description='',
                    unit_of_measure='',
                    timeseries_values=timeseries_values[header['id']]
                )
            )

        return models.snapshot.Snapshot(
            timestamp=datetime.datetime.now(),
            author=author,
            timeseries=timeseries
        )

    def snapshot_requester_ui(self):
        publications = self.get_publication_names()
        publication_id_choices = {
            publication["id"]: publication["category_name"]
            for publication in publications
            if publication["NoActive"] == 0
        }
        default_date_range = {"min": 2015, "max": 2025, "value": [2015, 2025]}

        return ui.div(
            ui.input_select(
                f"{self.get_ui_id()}_publication_id_select",
                "Выберите публикацию",
                publication_id_choices,
                selected=publications[0]["id"]
            ),
            ui.input_select(f"{self.get_ui_id()}_dataset_id_select",
                            "Выберите номер показателя", {}),
            ui.input_select(
                f"{self.get_ui_id()}_measure_id_select", "Выберите номер разреза", {}),
            ui.input_slider(
                f"{self.get_ui_id()}_date_range",
                "Выберите временной интервал",
                **default_date_range,
                sep="",
                ticks=True
            ),
            ui.input_action_button(
                f"{self.get_ui_id()}_request_snapshot_button", "Запросить выгрузку данных"),
        )

    def snapshot_requester_server(self, repository, snapshot_load_state, author):
        default_date_range = {"min": 2015, "max": 2025, "value": [2015, 2025]}

        def server_func(input, output, session):
            @reactive.effect
            @reactive.event(lambda bid=f"{self.get_ui_id()}_publication_id_select": getattr(input, bid)())
            def handle_publication_change():
                publication_id = getattr(
                    input, f"{self.get_ui_id()}_publication_id_select")()
                with reactive.isolate():
                    if publication_id is None:
                        ui.update_select(
                            f"{self.get_ui_id()}_dataset_id_select", choices={})
                        return

                    datasets = self.get_dataset_names(publication_id)
                    ui.update_select(
                        f"{self.get_ui_id()}_dataset_id_select",
                        choices={dataset["id"]: dataset["name"]
                                 for dataset in datasets}
                    )

            @reactive.effect
            @reactive.event(lambda bid=f"{self.get_ui_id()}_dataset_id_select": getattr(input, bid)())
            def handle_dataset_change():
                dataset_id = getattr(
                    input, f"{self.get_ui_id()}_dataset_id_select")()
                with reactive.isolate():
                    if dataset_id is None:
                        ui.update_select(
                            f"{self.get_ui_id()}_measure_id_select", choices={})
                        return

                    measures = self.get_measure_names(dataset_id)
                    ui.update_select(
                        f"{self.get_ui_id()}_measure_id_select",
                        choices={measure["id"]: measure["name"]
                                 for measure in measures['measure']}
                    )

            @reactive.effect
            @reactive.event(lambda bid=f"{self.get_ui_id()}_dataset_id_select": getattr(input, bid)(), lambda bid=f"{self.get_ui_id()}_measure_id_select": getattr(input, bid)())
            def handle_years_range_update():
                dataset_id = getattr(
                    input, f"{self.get_ui_id()}_dataset_id_select")()
                measure_id = getattr(
                    input, f"{self.get_ui_id()}_measure_id_select")()

                if dataset_id is None or measure_id is None:
                    ui.update_slider(
                        f"{self.get_ui_id()}_date_range", **default_date_range)
                    return

                years = self.get_years_range(dataset_id, measure_id)

                if years is None:
                    ui.update_slider(
                        f"{self.get_ui_id()}_date_range", **default_date_range)
                    return

                ui.update_slider(
                    f"{self.get_ui_id()}_date_range",
                    min=years[0]["FromYear"],
                    max=years[0]["ToYear"],
                    value=[years[0]["FromYear"], years[0]["ToYear"]]
                )

            @reactive.effect
            @reactive.event(lambda bid=f"{self.get_ui_id()}_request_snapshot_button": getattr(input, bid)(), ignore_init=True)
            def handle_request_snapshot():
                try:
                    publication_id = getattr(
                        input, f"{self.get_ui_id()}_publication_id_select")()
                    dataset_id = getattr(
                        input, f"{self.get_ui_id()}_dataset_id_select")()
                    measure_id = getattr(
                        input, f"{self.get_ui_id()}_measure_id_select")()
                    date_range = getattr(
                        input, f"{self.get_ui_id()}_date_range")()

                    kwargs = {
                        'publicationId': publication_id,
                        'datasetId': dataset_id,
                        'y1': date_range[0],
                        'y2': date_range[1],
                    }
                    if measure_id is not None:
                        kwargs['measureId'] = measure_id

                    print(kwargs)
                    snapshot = self.get_data(kwargs, author)
                    repository.insert_snapshot(snapshot, self.uuid)

                    # invalidating state
                    snapshot_load_state.set(snapshot_load_state.get() + 1)

                    ui.notification_show(
                        "Successfully loaded snapshot", type="message")
                except Exception as e:
                    ui.notification_show(
                        f"Failed to load snapshot: {e}", type="error")
                    traceback.format_exc()

        return server_func


class Comtrade_datasource(Datasource):
    name = "UN Comtrade"
    uuid = "8bf2ac0d-c97a-42a8-9930-d3ab58f39b09"
    description = """
    UN Comtrade is a comprehensive global trade database operated by the United Nations Statistics Division. It provides detailed import and export statistics reported by various countries. The UN Comtrade API is an interface that allows developers and researchers to access and utilize this vast amount of trade data programmatically.
    """

    def __init__(self, repository):
        super().__init__(repository)

    def get_data(self, kwargs, author):
        data = comtradeapicall.previewFinalData(**kwargs)
        return self.to_snapshot(data, author)

    def to_snapshot(self, df, author):
        df_group_keys = []
        print(len(df))
        for value in [
            'reporterCode',
            'partnerCode',
            'partner2Code',
            'motCode',
            'customsCode',
            'cmdCode'
        ]:
            if value in df.columns:
                df_group_keys.append(value)

        grouped = df.groupby(by=df_group_keys)
        timeseries = []

        for group_keys, group_df in grouped:
            name_dict = {}
            for value in [
                'reporterCode',
                'partnerCode',
                'partner2Code',
                'motCode',
                'customsCode',
                'cmdCode'
            ]:
                if value in group_df.columns and not df[value].isnull().all():
                    name_dict[value] = str(group_df[value].iloc[0])

            df_primary = group_df[['period', 'primaryValue']].rename(
                columns={'primaryValue': 'value'})
            df_fob = group_df[['period', 'fobvalue']].rename(
                columns={'fobvalue': 'value'})
            df_cif = group_df[['period', 'cifvalue']].rename(
                columns={'cifvalue': 'value'})

            name_suffix_to_df = {
                'primary': df_primary,
                'fob': df_fob,
                'cif': df_cif
            }

            for name_suffix, value_df in name_suffix_to_df.items():
                tsv = []
                for row in value_df.itertuples():
                    date = pd.to_datetime(
                        row.period, format='%Y%m').date().replace(day=1)
                    tsv.append(models.timeseries.TimeseriesValue(
                        timestamp=date, value=row.value))

                name = dict(name_dict)
                name['valueType'] = name_suffix
                timeseries.append(
                    models.timeseries.Timeseries(
                        name=ordered_dict_to_string(name),
                        description='',
                        unit_of_measure='',
                        timeseries_values=tsv
                    )
                )

        if len(timeseries) == 0:
            raise ValueError("No data found")

        return models.snapshot.Snapshot(
            timestamp=datetime.datetime.now(),
            author=author,
            timeseries=timeseries
        )

    def snapshot_requester_ui(self):
        countries = {
            country.numeric: country.name for country in pycountry.countries}

        return ui.layout_columns(
            ui.div(
                ui.input_selectize(
                    f"{self.get_ui_id()}_type_code",
                    "Type of trade",
                    choices={"C": "Commodities", "S": "Services"},
                    selected='C'
                ),
                ui.input_selectize(
                    f"{self.get_ui_id()}_frequency_code",
                    "Trade frequency",
                    choices={"A": "Annual", "M": "Monthly"},
                    selected="M"
                ),
                ui.input_selectize(
                    f"{self.get_ui_id()}_classification_code",
                    "Trade classification",
                    choices={
                        "HS": "Harmonized System",
                        "SITC": "SITC",
                        "BEC": "BEC",
                        "EBOPS": "EBOPS"
                    },
                    selected='HS'
                ),
                ui.input_selectize(
                    f"{self.get_ui_id()}_reporter_code",
                    "Reporter country",
                    choices=countries,
                    multiple=True,
                    selected=36
                ),
                ui.input_date_range(
                    f"{self.get_ui_id()}_period",
                    "Data period",
                    format="yyyymm",
                    start='2022-06-01',
                    end='2022-07-01'
                ),
            ),
            ui.div(
                ui.input_text(
                    f"{self.get_ui_id()}_partner_code", "Partner code"),
                ui.input_text(
                    f"{self.get_ui_id()}_partner2_code", "Partner 2 code"),
                ui.input_text(f"{self.get_ui_id()}_commodity_code",
                              "Commodity code", value=91),
                ui.input_text(f"{self.get_ui_id()}_trade_flow_code",
                              "Trade flow code", value='M'),
                ui.input_text(
                    f"{self.get_ui_id()}_customs_code", "Customs code"),
                ui.input_text(f"{self.get_ui_id()}_mot_code",
                              "Mode of transport code"),
            ),
            ui.input_action_button(
                f"{self.get_ui_id()}_request_snapshot_button", "Request Snapshot"),
            col_widths={"sm": (6, 6, 12)},
        )

    def snapshot_requester_server(self, repository, snapshot_load_state, author):
        def server_func(input, output, session):
            @reactive.effect
            @reactive.event(lambda bid=f"{self.get_ui_id()}_request_snapshot_button": getattr(input, bid)(), ignore_init=True)
            def handle_request_snapshot():
                try:
                    period = getattr(input, f"{self.get_ui_id()}_period")()
                    start = period[0].replace(day=1)
                    end = period[1].replace(day=1)
                    period_tuned = ','.join(pd.date_range(
                        start=start, end=end, freq='MS').strftime('%Y%m'))

                    type_code = getattr(
                        input, f"{self.get_ui_id()}_type_code")()
                    frequency_code = getattr(
                        input, f"{self.get_ui_id()}_frequency_code")()
                    classification_code = getattr(
                        input, f"{self.get_ui_id()}_classification_code")()
                    reporter_code = getattr(
                        input, f"{self.get_ui_id()}_reporter_code")()
                    partner_code = getattr(
                        input, f"{self.get_ui_id()}_partner_code")()
                    partner2_code = getattr(
                        input, f"{self.get_ui_id()}_partner2_code")()
                    commodity_code = getattr(
                        input, f"{self.get_ui_id()}_commodity_code")()
                    trade_flow_code = getattr(
                        input, f"{self.get_ui_id()}_trade_flow_code")()
                    customs_code = getattr(
                        input, f"{self.get_ui_id()}_customs_code")()
                    mot_code = getattr(input, f"{self.get_ui_id()}_mot_code")()

                    kwargs = {
                        'typeCode': type_code,
                        'freqCode': frequency_code,
                        'clCode': classification_code,
                        'reporterCode': ','.join(reporter_code) if reporter_code else None,
                        'period': period_tuned,
                        'partnerCode': partner_code if partner_code else None,
                        'partner2Code': partner2_code if partner2_code else None,
                        'cmdCode': commodity_code if commodity_code else None,
                        'flowCode': trade_flow_code if trade_flow_code else None,
                        'customsCode': customs_code if customs_code else None,
                        'motCode': mot_code if mot_code else None,
                    }

                    print(kwargs)
                    snapshot = self.get_data(kwargs, author)
                    repository.insert_snapshot(snapshot, self.uuid)

                    # invalidating state
                    snapshot_load_state.set(snapshot_load_state.get() + 1)

                    ui.notification_show(
                        "Successfully loaded snapshot", type="message")
                except Exception as e:
                    ui.notification_show(
                        f"Failed to load snapshot: {e}", type="error")
                    print(traceback.format_exc())
        return server_func


class Worldbank_datasource(Datasource):
    name = "World Bank Report API"
    uuid = "20d9bb72-a9cb-46ba-a07a-eaf0195621f0"
    description = "The World Bank Documents & Reports API is a powerful tool provided by The World Bank that allows developers and researchers to access a vast repository of official documents and reports related to the Bank international development projects and economic research. This API facilitates programmatic access to a wealth of information, providing users with the ability to integrate and analyze data seamlessly within their applications or research."

    base_url = "https://api.worldbank.org/v2"

    def __init__(self, repository):
        super().__init__(repository)

    def get_data(self, kwargs, author):
        url = f"{self.base_url}/country/{';'.join(kwargs['countries'])}/indicator/{kwargs['indicator']}"
        data = requests.get(url, kwargs['params'])
        return self.to_snapshot(data.json(), author)

    def to_snapshot(self, json_, author):
        print(json_)
        # assert len(json_) == 2

        timeseries_values = {}
        for record in json_[1]:
            key = ordered_dict_to_string({
                'indicator': record['indicator']['id'],
                'country': record['country']['id']
            })
            if key not in timeseries_values.keys():
                timeseries_values[key] = []
            timeseries_values[key].append(
                models.timeseries.TimeseriesValue(
                    timestamp=datetime.date(int(record['date']), 1, 1),
                    value=record['value']
                )
            )

        timeseries = []
        for key, values in timeseries_values.items():
            timeseries.append(
                models.timeseries.Timeseries(
                    name=key,
                    description='',
                    unit_of_measure='',
                    timeseries_values=values
                )
            )

        return models.snapshot.Snapshot(
            timestamp=datetime.datetime.now(),
            author=author,
            timeseries=timeseries
        )

    def snapshot_requester_ui(self):
        countries = {
            country.alpha_3: country.name for country in pycountry.countries}

        return ui.layout_columns(
            ui.input_selectize(f"{self.get_ui_id()}_countries",
                               "Countries", choices=countries, multiple=True),
            ui.input_text(f"{self.get_ui_id()}_indicator",
                          "Indicator", value="SP.POP.TOTL"),
            ui.input_action_button(
                f"{self.get_ui_id()}_request_snapshot_button", "Request Snapshot"),
            col_widths={"sm": (12)},
        )

    def snapshot_requester_server(self, repository, snapshot_load_state, author):
        def server_func(input, output, session):
            @reactive.effect
            @reactive.event(lambda bid=f"{self.get_ui_id()}_request_snapshot_button": getattr(input, bid)(), ignore_init=True)
            def handle_request_snapshot():
                try:
                    countries = getattr(
                        input, f"{self.get_ui_id()}_countries")()
                    indicator = getattr(
                        input, f"{self.get_ui_id()}_indicator")()

                    if not countries:
                        ui.notification_show(
                            "Please select at least one country", type="error")
                        return

                    if not indicator:
                        ui.notification_show(
                            "Please enter an indicator", type="error")
                        return

                    kwargs = {
                        'indicator': indicator,
                        'countries': countries,
                        'params': {
                            'format': 'json',
                            'per_page': 10000,
                        }
                    }

                    print(kwargs)
                    snapshot = self.get_data(kwargs, author)
                    print(snapshot)
                    repository.insert_snapshot(snapshot, self.uuid)

                    # invalidating state
                    snapshot_load_state.set(snapshot_load_state.get() + 1)

                    ui.notification_show(
                        "Successfully loaded snapshot", type="message")
                except Exception as e:
                    ui.notification_show(
                        f"Failed to load snapshot: {e}", type="error")
                    print(traceback.format_exc())
        return server_func
