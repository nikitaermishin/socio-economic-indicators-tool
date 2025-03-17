ATTACH TABLE _ UUID '5a4320f7-be0d-4321-b768-d5f1a4bb5312'
(
    `uuid` UUID,
    `name` String,
    `description` String,
    `unit_of_measure` String,
    `snapshot_uuid` UUID
)
ENGINE = MergeTree
PRIMARY KEY uuid
ORDER BY uuid
SETTINGS index_granularity = 8192
