-- Таблица для значений временных рядов
CREATE TABLE TimeSeriesValue (
    timestamp DateTime,
    value Float64,
    timeseries_uuid UUID,
    PRIMARY KEY (timestamp, timeseries_uuid)
) ENGINE = MergeTree()
ORDER BY (timestamp, timeseries_uuid);

-- Таблица для временных рядов
CREATE TABLE TimeSeries (
    uuid UUID,
    name String,
    description String,
    unit_of_measure String,
    snapshot_uuid UUID,
    PRIMARY KEY uuid
) ENGINE = MergeTree()
ORDER BY uuid;

-- Таблица для слепков
CREATE TABLE Snapshot (
    uuid UUID,
    timestamp DateTime,
    datasource_uuid UUID,
    PRIMARY KEY uuid
) ENGINE = MergeTree()
ORDER BY uuid;

-- Таблица для источников данных
CREATE TABLE DataSource (
    uuid UUID,
    name String,
    PRIMARY KEY uuid
) ENGINE = MergeTree()
ORDER BY uuid;