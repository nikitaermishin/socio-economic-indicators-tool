-- Таблица для значений временных рядов
CREATE TABLE IF NOT EXISTS socio_economic_indicators_tool.TimeSeriesValue (
    timestamp DateTime64,
    value Nullable(Float64),
    timeseries_uuid UUID,
    PRIMARY KEY (timestamp, timeseries_uuid)
) ENGINE = MergeTree()
ORDER BY (timestamp, timeseries_uuid);

-- Таблица для временных рядов
CREATE TABLE IF NOT EXISTS socio_economic_indicators_tool.TimeSeries (
    uuid UUID,
    name String,
    description String,
    unit_of_measure String,
    snapshot_uuid UUID,
) ENGINE = MergeTree()
ORDER BY uuid
PRIMARY KEY uuid;

-- Таблица для слепков
CREATE TABLE IF NOT EXISTS socio_economic_indicators_tool.Snapshot (
    uuid UUID,
    name String,
    description String,
    author String,
    timestamp DateTime,
    datasource_uuid UUID,
) ENGINE = MergeTree()
ORDER BY uuid
PRIMARY KEY uuid;

-- Таблица для источников данных
CREATE TABLE IF NOT EXISTS socio_economic_indicators_tool.DataSource (
    uuid UUID,
    name String,
    description String,
) ENGINE = MergeTree()
ORDER BY uuid
PRIMARY KEY uuid;