import pandas as pd
import json
import uuid
import datetime

import models.timeseries


class Snapshot:
    name: str
    description: str
    timestamp: datetime.datetime
    uuid: str
    timeseries: list[models.timeseries.Timeseries]
    author: str

    def __init__(self, timestamp, author, timeseries, uuid_=None):
        self.timestamp = timestamp
        if uuid_ is None:
            uuid_ = uuid.uuid4()
        self.uuid = uuid_
        self.author = author
        self.timeseries = timeseries

    def serialize(self):
        return {
            # "name": self.name,
            # "description": self.description,
            "timestamp": str(self.timestamp),
            "uuid": self.uuid,
            "author": self.author,
            "data": json.loads(
                self.to_dataframe().to_json(orient="records", force_ascii=False)
            )
        }

    def to_dataframe(self):
        assert len(self.timeseries) != 0
        index = [tsv.timestamp for tsv in self.timeseries[0].timeseries_values]

        data = {
            ts.name: [tsv.value for tsv in ts.timeseries_values]
            for ts in self.timeseries
        }
        return pd.DataFrame(data=data, index=index)
