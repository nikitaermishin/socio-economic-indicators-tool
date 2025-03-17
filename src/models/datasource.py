from uuid import UUID
import requests
import json
import datetime

import models.snapshot
import models.timeseries

import traceback

from shiny import reactive
from shiny.express import input, ui, render, module

class Datasource:
    name: str
    uuid: str
    description: str

    def __init__(self, repository):
        UUID(self.uuid, version=4)
        repository.try_insert_datasource(self.uuid, self.name, self.description)

    def snapshot_requester(self, id, repository, snapshot_load_state):
        pass

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

    def get_data(self, kwargs):
        """
        Достаем данные по API ЦБ РФ
        Дока https://cbr.ru/statistics/data-service/APIdocumentation/
        """
        def build_request(kwargs):
            return self.base_url + "/data?" + "&".join([f"{key}={value}" for key, value in kwargs.items()])

        response = requests.get(build_request(kwargs))
        response.raise_for_status()

        print(response.text)
        snapshot = self.to_snapshot(json.loads(response.text))

        print('\n\n\n\n\n')
        print (snapshot.asdict())
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

    def to_snapshot(self, json_):
        assert len(json_['SType']) == 1

        timeseries_values: dict[int, models.timeseries.TimeseriesValue] = {}
        for data_elem in json_['RawData']:
            elem_id = data_elem['element_id']
            if elem_id not in timeseries_values:
                timeseries_values[elem_id] = []
            timeseries_values[elem_id].append(models.timeseries.TimeseriesValue(timestamp=data_elem['date'], value=data_elem['obs_val']))

        snapshot_name = json_['SType'][0]['dsName'] + ' - ' + json_['SType'][0]['PublName']
        timeseries: list[models.timeseries.Timeseries] = []
        for header in json_['headerData']:
            name = header['elname']
            timeseries.append(models.timeseries.Timeseries(name=name, description='', unit_of_measure='', timeseries_values=timeseries_values[header['id']]))

        return models.snapshot.Snapshot(timestamp=datetime.datetime.now(), timeseries=timeseries)
    
    def snapshot_requester(self, id, repository, snapshot_load_state):
        @module
        def _(input, output, session):
            publications = self.get_publication_names()
            publication_id_choices = {publication["id"]: publication["category_name"] for publication in publications if publication["NoActive"] == 0}

            default_date_range = {"min":2015, "max":2025, "value":[2015, 2025]}

            @render.express
            def _():
                ui.input_select("publication_id_select", "Выберите публикацию", publication_id_choices, selected=publications[0]["id"])
                ui.input_select("dataset_id_select", "Выберите номер показателя", {})
                ui.input_select("measure_id_select", "Выберите номер разреза", {})
                ui.input_slider("date_range", "Выберите временной интервал", **default_date_range, sep="", ticks=True)
                ui.input_action_button("request_snapshot_button", "Запросить выгрузку данных")

            @reactive.effect
            @reactive.event(input.publication_id_select)
            def _():
                publication_id = input.publication_id_select()
                with reactive.isolate():
                    if publication_id is None:
                        ui.update_select("dataset_id_select", choices={})
                        return

                    datasets = self.get_dataset_names(publication_id)
                    ui.update_select("dataset_id_select", choices={dataset["id"]: dataset["name"] for dataset in datasets})

            @reactive.effect
            @reactive.event(input.dataset_id_select)
            def _():
                dataset_id = input.dataset_id_select()
                with reactive.isolate():
                    if dataset_id is None:
                        ui.update_select("measure_id_select", choices={})
                        return
                    
                    measures = self.get_measure_names(dataset_id)
                    ui.update_select("measure_id_select", choices={measure["id"]: measure["name"] for measure in measures['measure']})

            @reactive.effect
            @reactive.event(input.dataset_id_select, input.measure_id_select)
            def _():
                dataset_id = input.dataset_id_select()
                measure_id = input.measure_id_select()
                
                if dataset_id is None or measure_id is None:
                    ui.update_slider("date_range", **default_date_range)
                    return
                    
                years = self.get_years_range(dataset_id, measure_id)

                if years is None:
                    ui.update_slider("date_range", **default_date_range)
                    return

                ui.update_slider("date_range", min=years[0]["FromYear"], max=years[0]["ToYear"], value=[years[0]["FromYear"], years[0]["ToYear"]])

            @reactive.effect
            @reactive.event(input.request_snapshot_button, ignore_init=True)
            def _():
                try:
                    kwargs = {
                        'publicationId': input.publication_id_select(),
                        'datasetId': input.dataset_id_select(),
                        'y1': input.date_range()[0],
                        'y2': input.date_range()[1],
                    }
                    if input.measure_id_select() is not None:
                        kwargs['measureId'] = input.measure_id_select()

                    print(kwargs)
                    snapshot = self.get_data(kwargs)
                    repository.insert_snapshot(snapshot, self.uuid)

                    #invalidating state
                    snapshot_load_state.set(snapshot_load_state.get() + 1)

                    ui.notification_show(f"Successfully loaded snapshot", type="message")
                except Exception as e:
                    ui.notification_show(f"Failed to load snapshot: {e}", type="error")
                    traceback.format_exc()

        return _(id)


class Comtrade_datasource(Datasource):
    name = "UN Comtrade"
    uuid = "8bf2ac0d-c97a-42a8-9930-d3ab58f39b09"
    description = """
    UN Comtrade is a comprehensive global trade database operated by the United Nations Statistics Division. It provides detailed import and export statistics reported by various countries. The UN Comtrade API is an interface that allows developers and researchers to access and utilize this vast amount of trade data programmatically.
    """


class Worldbank_datasource(Datasource):
    name = "World Bank Report API"
    uuid = "20d9bb72-a9cb-46ba-a07a-eaf0195621f0"
    description = """
    The World Bank Documents & Reports API is a powerful tool provided by The World Bank that allows developers and researchers to access a vast repository of official documents and reports related to the Bank's international development projects and economic research. This API facilitates programmatic access to a wealth of information, providing users with the ability to integrate and analyze data seamlessly within their applications or research.
    """