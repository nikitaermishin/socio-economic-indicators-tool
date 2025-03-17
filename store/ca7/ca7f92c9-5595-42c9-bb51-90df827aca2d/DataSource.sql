ATTACH TABLE _ UUID 'e224c224-9682-4fa0-b8b7-701b7ad999d8'
(
    `uuid` UUID,
    `name` String,
    `description` String
)
ENGINE = MergeTree
PRIMARY KEY uuid
ORDER BY uuid
SETTINGS index_granularity = 8192
