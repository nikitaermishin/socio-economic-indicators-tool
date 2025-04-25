import clickhouse_connect
import pandas as pd
import traceback
import datetime

import models.timeseries
import models.snapshot


class TimeSeriesRepository:
    def __init__(self):
        try:
            self.client = clickhouse_connect.get_client(
                host='localhost',
                username='default',
                database='socio_economic_indicators_tool'
            )
        except Exception as exc:
            print(exc)

    def get_snapshots(self, datasource_names=[], lower_timestamp=None, upper_timestamp=None, limit=9999):
        try:
            datasource_names_str = ', '.join(
                f"'{name}'" for name in datasource_names)

            query = f"""
            SELECT s.uuid, s.timestamp, d.name, s.author
            FROM Snapshot s
            JOIN DataSource d ON s.datasource_uuid = d.uuid
            WHERE 1=1
            {(f"AND d.name IN ({datasource_names_str})" if datasource_names else "")}
            {(f"AND s.timestamp &gt;= '{lower_timestamp}'" if lower_timestamp else "")}
            {(f"AND s.timestamp &lt;= '{upper_timestamp}'" if upper_timestamp else "")}
            LIMIT {limit}"""

            print(query)

            result = self.client.query(query)
            print('DEBUG: get_snapshots')
            return pd.DataFrame(data=result.result_rows, columns=result.column_names)

        except Exception as exc:
            print('exc')
            print(exc)

    def get_datasource_info(self, datasource_uuid: str):
        print('DEBUG: get_datasource_info')

        datasource_info = {}

        last_snapshot_query = f"""
            SELECT 
                s.timestamp,
                s.author
            FROM 
                Snapshot s
            JOIN 
                DataSource d ON s.datasource_uuid = d.uuid
            WHERE 
                d.uuid = '{datasource_uuid}'
            ORDER BY 
                s.timestamp DESC
            LIMIT 1
        """

        last_snapshot_result = self.client.query(last_snapshot_query)
        if last_snapshot_result.result_rows:
            datasource_info['last_snapshot_timestamp'] = str(
                last_snapshot_result.result_rows[0][0])
            datasource_info['last_snapshot_author'] = last_snapshot_result.result_rows[0][1]

        snapshots_count_query = f"""
            SELECT COUNT(*) FROM Snapshot s2 WHERE s2.datasource_uuid = '{datasource_uuid}'
        """

        snapshots_count_result = self.client.query(snapshots_count_query)
        datasource_info['snapshots_count'] = snapshots_count_result.result_rows[0][0]

        return datasource_info

    def try_insert_datasource(self, uuid: str, name: str, description: str):
        try:
            print('DEBUG: try_insert_datasource')

            exists_query = f"SELECT count(*) FROM socio_economic_indicators_tool.DataSource WHERE uuid = '{uuid}'"
            result = self.client.query(exists_query)
            if result.result_rows[0][0] != 0:
                return

            query = f"""
            INSERT INTO socio_economic_indicators_tool.DataSource (uuid, name, description)
            VALUES ('{uuid}', '{name}', '{description}')
            """
            self.client.query(query)
        except Exception as exc:
            print('exc')
            print(exc)

    def insert_snapshot(self, snapshot: models.snapshot.Snapshot, datasource_uuid):
        print('DEBUG: insert_snapshot')
        query = f"""
        INSERT INTO socio_economic_indicators_tool.Snapshot (uuid, timestamp, datasource_uuid, author)
        VALUES ('{snapshot.uuid}', '{snapshot.timestamp}', '{datasource_uuid}', '{snapshot.author}')
        """
        self.client.query(query)

        self.__insert_timeseries_batch(snapshot.timeseries, snapshot.uuid)

    def __insert_timeseries_batch(self, timeseries_list, snapshot_uuid: str):
        print('DEBUG: __insert_timeseries_batch')

        # 1. Подготовка данных для временных рядов (список словарей)
        timeseries_values = []
        timeseries_columns = ['uuid', 'name',
                              'description', 'unit_of_measure', 'snapshot_uuid']
        for ts in timeseries_list:
            timeseries_values.append([
                ts.uuid,
                ts.name,
                ts.description,
                ts.unit_of_measure,
                snapshot_uuid
            ])

        # Пакетная вставка временных рядов
        if timeseries_values:
            print(f"Inserting {len(timeseries_values)} timeseries")

            self.client.insert(
                'socio_economic_indicators_tool.TimeSeries',
                timeseries_values,
                column_names=timeseries_columns
            )

        # 2. Подготовка и вставка всех значений временных рядов
        tsv_columns = ['timestamp', 'value', 'timeseries_uuid']
        tsv_values = []
        for ts in timeseries_list:
            for value in ts.timeseries_values:
                tsv_values.append([
                    datetime.datetime.combine(
                        value.timestamp, datetime.datetime.min.time()),
                    value.value,
                    ts.uuid
                ])

        # Пакетная вставка значений (если есть)
        if tsv_values:
            print(f"Inserting {len(tsv_values)} timeseries values")

            self.client.insert(
                'socio_economic_indicators_tool.TimeSeriesValue',
                tsv_values,
                column_names=tsv_columns
            )

    def get_snapshot_by_uuid(self, uuid: str):
        try:
            print('DEBUG: get_snapshot_by_uuid')
            tsv_query = f"""
            SELECT
                ts.uuid,
                tsv.timestamp, 
                tsv.value 
            FROM 
                socio_economic_indicators_tool.TimeSeries AS ts
            JOIN 
                socio_economic_indicators_tool.TimeSeriesValue AS tsv ON ts.uuid = tsv.timeseries_uuid
            WHERE 
                ts.snapshot_uuid = '{uuid}'
            """
            tsv_result = self.client.query(tsv_query)
            print('tsv_len', len(tsv_result.result_rows))

            tsv_dict = {}
            for row in tsv_result.result_rows:
                ts_uuid, timestamp, value = row[0], row[1], row[2]

                if ts_uuid not in tsv_dict:
                    tsv_dict[ts_uuid] = []
                tsv_dict[row[0]].append(
                    {'timestamp': timestamp, 'value': value})

            ts_query = f"""
            SELECT 
                ts.uuid, ts.name, ts.description, ts.unit_of_measure 
            FROM 
                socio_economic_indicators_tool.TimeSeries ts 
            WHERE 
                ts.snapshot_uuid = '{uuid}'
            """
            ts_result = self.client.query(ts_query)
            print('ts_len', len(ts_result.result_rows))

            ts_list = []
            for row in ts_result.result_rows:
                ts_uuid, name, description, unit_of_measure = row[0], row[1], row[2], row[3]

                ts_list.append(models.timeseries.Timeseries(
                    uuid_=ts_uuid,
                    name=name,
                    description=description,
                    unit_of_measure=unit_of_measure,
                    timeseries_values=[
                        models.timeseries.TimeseriesValue(
                            timestamp=tsv['timestamp'],
                            value=tsv['value']
                        ) for tsv in tsv_dict[ts_uuid]
                    ]
                ))

            s_query = f"""
            SELECT s.timestamp, s.author 
            FROM socio_economic_indicators_tool.Snapshot s 
            WHERE s.uuid = '{uuid}'
            LIMIT 1
            """
            s_result = self.client.query(s_query)

            return models.snapshot.Snapshot(
                timestamp=s_result.result_rows[0][0],
                author=s_result.result_rows[0][1],
                timeseries=ts_list,
                uuid_=uuid
            )

        except Exception as exc:
            # print('exc')
            traceback.print_exc()

    def __del__(self):
        pass
