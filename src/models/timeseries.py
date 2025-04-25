import uuid
import datetime


class TimeseriesValue:
    timestamp: datetime.date
    value: float

    def __init__(self, timestamp, value):
        self.timestamp = timestamp
        self.value = value

    def asdict(self):
        return {
            "timestamp": self.timestamp,
            "value": self.value
        }


class Timeseries:
    name: str
    description: str
    unit_of_measure: str
    uuid: str
    timeseries_values: list[TimeseriesValue]

    def __init__(self, name, description, unit_of_measure, timeseries_values, uuid_=None):
        self.name = name
        self.description = description
        self.unit_of_measure = unit_of_measure
        self.timeseries_values = timeseries_values
        if uuid_ is None:
            uuid_ = uuid.uuid4()
        self.uuid = uuid_

    def asdict(self):
        return {
            "name": self.name,
            "description": self.description,
            "unit_of_measure": self.unit_of_measure,
            "uuid": self.uuid,
            "timeseries_values": [value.asdict() for value in self.timeseries_values]
        }
