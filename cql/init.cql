CREATE KEYSPACE IF NOT EXISTS gridsense
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 1
};

USE gridsense;

-- Table 1: Optimised for queries by specific sensor
CREATE TABLE IF NOT EXISTS sensor_readings (
    sensor_id TEXT,
    reading_time TIMESTAMP,
    metric_type TEXT,
    value FLOAT,
    unit TEXT,
    quality_flag TINYINT,
    PRIMARY KEY ((sensor_id), reading_time)
) WITH CLUSTERING ORDER BY (reading_time DESC)
AND default_time_to_live = 7776000;

-- Table 2: Relay operation log
CREATE TABLE IF NOT EXISTS relay_events (
    feeder_id TEXT,
    event_time TIMEUUID,
    relay_id TEXT,
    event_type TEXT,
    fault_type TEXT,
    current_kA FLOAT,
    PRIMARY KEY ((feeder_id), event_time)
) WITH CLUSTERING ORDER BY (event_time ASC);

-- SOLVING THE TODO: Second table for cross-network dashboard
CREATE TABLE IF NOT EXISTS sensor_readings_by_metric (
    metric_type TEXT,
    reading_time TIMESTAMP,
    sensor_id TEXT,
    value FLOAT,
    unit TEXT,
    quality_flag TINYINT,
    PRIMARY KEY ((metric_type), reading_time, sensor_id)
) WITH CLUSTERING ORDER BY (reading_time DESC);