import pandas as pd
import models.timeseries
import uuid

class Snapshot:
    name: str
    description: str
    timestamp: str
    uuid: str
    timeseries: list[models.timeseries.Timeseries]

    def __init__(self, timestamp, timeseries):
        self.timestamp = timestamp
        self.uuid = uuid.uuid4()

        self.timeseries = timeseries

    def asdict(self):
        pass
        return {
            # "name": self.name,
            "timestamp": self.timestamp,
            "timeseries": [timeseries.asdict() for timeseries in self.timeseries]
        }
    
    def to_dataframe(self):
        assert len(self.timeseries) != 0
        index = [tsv.timestamp for tsv in self.timeseries[0].timeseries_values]

        data = {ts.name : [tsv.value for tsv in ts.timeseries_values] for ts in self.timeseries}
        return pd.DataFrame(data=data, index=index)