-- Таблица для значений временных рядов
CREATE TABLE IF NOT EXISTS TimeSeriesValue (
    timestamp DateTime,
    value Float64,
    timeseries_uuid UUID,
    PRIMARY KEY (timestamp, timeseries_uuid)
) ENGINE = MergeTree()
ORDER BY (timestamp, timeseries_uuid);

-- Таблица для временных рядов
CREATE TABLE IF NOT EXISTS TimeSeries (
    uuid UUID,
    name String,
    description String,
    unit_of_measure String,
    snapshot_uuid UUID,
) ENGINE = MergeTree()
ORDER BY uuid
PRIMARY KEY uuid;

-- Таблица для слепков
CREATE TABLE IF NOT EXISTS Snapshot (
    uuid UUID,
    name String,
    description String,
    load_author String,
    timestamp DateTime,
    datasource_uuid UUID,
) ENGINE = MergeTree()
ORDER BY uuid
PRIMARY KEY uuid;

-- Таблица для источников данных
CREATE TABLE IF NOT EXISTS DataSource (
    uuid UUID,
    name String,
    description String,
) ENGINE = MergeTree()
ORDER BY uuid
PRIMARY KEY uuid;