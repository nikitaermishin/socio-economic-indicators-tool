ATTACH TABLE _ UUID '9564b649-3b6a-4384-a63e-3d999f7c76d9'
(
    `uuid` UUID,
    `timestamp` DateTime,
    `datasource_uuid` UUID
)
ENGINE = MergeTree
PRIMARY KEY uuid
ORDER BY uuid
SETTINGS index_granularity = 8192
