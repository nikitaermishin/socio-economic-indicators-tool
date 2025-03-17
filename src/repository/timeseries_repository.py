import clickhouse_connect
import pandas as pd

import models.timeseries
import models.snapshot

import traceback

class TimeSeriesRepository:
    def __init__(self):
        try:
            self.client = clickhouse_connect.get_client(host='localhost', username='default', database='socio_economic_indicators_tool')
        except Exception as exc:
            print(exc)

    def get_snapshots(self, datasource_names=[], lower_timestamp=None, upper_timestamp=None, limit=9999):
        try:
            datasource_names_str = ', '.join(f"'{name}'" for name in datasource_names)

            query = f"""
            SELECT s.uuid, s.timestamp, d.name
            FROM Snapshot s
            JOIN DataSource d ON s.datasource_uuid = d.uuid
            WHERE 1=1
            {(f"AND d.name IN ({datasource_names_str})" if datasource_names else "")}
            {(f"AND s.timestamp >= '{lower_timestamp}'" if lower_timestamp else "")}
            {(f"AND s.timestamp <= '{upper_timestamp}'" if upper_timestamp else "")}
            LIMIT {limit}"""

            print(query)

            result = self.client.query(query)
            print('DEBUG: get_snapshots')
            return pd.DataFrame(data=result.result_rows, columns=result.column_names)

        except Exception as exc:
            print('exc')
            print(exc)

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
        INSERT INTO socio_economic_indicators_tool.Snapshot (uuid, timestamp, datasource_uuid)
        VALUES ('{snapshot.uuid}', '{snapshot.timestamp}', '{datasource_uuid}')
        """
        self.client.query(query)

        for timeseries in snapshot.timeseries:
            self.__insert_timeseries(timeseries, snapshot.uuid)

    def __insert_timeseries(self, timeseries: models.timeseries.Timeseries, snapshot_uuid: str):
        print('DEBUG: __insert_timeseries')
        query = f"""
        INSERT INTO socio_economic_indicators_tool.TimeSeries (uuid, name, description, unit_of_measure, snapshot_uuid)
        VALUES ('{timeseries.uuid}', '{timeseries.name}', '{timeseries.description}', '{timeseries.unit_of_measure}', '{snapshot_uuid}')
        """
        self.client.query(query)

        for value in timeseries.timeseries_values:
            self.__insert_timeseries_value(value, timeseries.uuid)

    def __insert_timeseries_value(self, value: models.timeseries.TimeseriesValue, timeseries_uuid: str):
        print('DEBUG: __insert_timeseries_value')
        print(value.timestamp, value.value, timeseries_uuid)
        query = f"""
        INSERT INTO socio_economic_indicators_tool.TimeSeriesValue (timestamp, value, timeseries_uuid)
        VALUES ('{value.timestamp}', '{value.value}', '{timeseries_uuid}')
        """
        self.client.query(query)

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
                tsv_dict[row[0]].append({'timestamp': timestamp, 'value': value})

            ts_query = f"""
            SELECT ts.uuid, ts.name, ts.description, ts.unit_of_measure FROM socio_economic_indicators_tool.TimeSeries ts WHERE ts.snapshot_uuid = '{uuid}'
            """
            ts_result = self.client.query(ts_query)
            print('ts_len', len(ts_result.result_rows))


            ts_list = []
            for row in ts_result.result_rows:
                ts_uuid, name, description, unit_of_measure = row[0], row[1], row[2], row[3]

                ts_list.append(models.timeseries.Timeseries(
                    uuid=ts_uuid,
                    name=name,
                    description=description,
                    unit_of_measure=unit_of_measure,
                    timeseries_values=[models.timeseries.TimeseriesValue(
                        timestamp=tsv['timestamp'],
                        value=tsv['value']
                    ) for tsv in tsv_dict[ts_uuid]]
                ))

            return models.snapshot.Snapshot(
                timestamp='',
                timeseries=ts_list
            )


        except Exception as exc:
            # print('exc')
            traceback.print_exc()

    def __del__(self):
        pass