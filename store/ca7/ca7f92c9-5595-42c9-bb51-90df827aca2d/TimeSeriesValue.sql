ATTACH TABLE _ UUID 'e51da332-bd9e-4bd8-b656-4a6ed60664bc'
(
    `timestamp` DateTime,
    `value` Float64,
    `timeseries_uuid` UUID
)
ENGINE = MergeTree
PRIMARY KEY (timestamp, timeseries_uuid)
ORDER BY (timestamp, timeseries_uuid)
SETTINGS index_granularity = 8192
