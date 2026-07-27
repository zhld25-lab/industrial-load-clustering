PRAGMA foreign_keys = ON;

CREATE TABLE dataset_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE parks (
    park_id TEXT PRIMARY KEY,
    park_name TEXT NOT NULL,
    region TEXT NOT NULL,
    timezone TEXT NOT NULL,
    data_classification TEXT NOT NULL CHECK (data_classification = 'synthetic')
);

CREATE TABLE facilities (
    facility_id TEXT PRIMARY KEY,
    park_id TEXT NOT NULL REFERENCES parks(park_id),
    facility_type TEXT NOT NULL,
    industry_segment TEXT NOT NULL,
    contracted_capacity_kw REAL NOT NULL CHECK (contracted_capacity_kw > 0),
    equipment_efficiency REAL NOT NULL CHECK (equipment_efficiency BETWEEN 0 AND 1)
);

CREATE TABLE load_measurements (
    facility_id TEXT NOT NULL REFERENCES facilities(facility_id),
    timestamp TEXT NOT NULL,
    gross_load_kw REAL,
    renewable_generation_kw REAL NOT NULL CHECK (renewable_generation_kw >= 0),
    net_load_kw REAL,
    temperature_c REAL NOT NULL,
    tariff_usd_kwh REAL NOT NULL CHECK (tariff_usd_kwh >= 0),
    is_weekend INTEGER NOT NULL CHECK (is_weekend IN (0, 1)),
    is_anomaly INTEGER NOT NULL CHECK (is_anomaly IN (0, 1)),
    quality_flag TEXT NOT NULL CHECK (quality_flag IN ('valid', 'anomaly', 'missing')),
    data_source TEXT NOT NULL CHECK (data_source = 'synthetic_generator_v1'),
    PRIMARY KEY (facility_id, timestamp)
);

CREATE INDEX idx_load_timestamp ON load_measurements(timestamp);
CREATE INDEX idx_load_quality ON load_measurements(quality_flag);

CREATE VIEW v_park_hourly_load AS
SELECT timestamp,
       SUM(gross_load_kw) AS gross_load_kw,
       SUM(renewable_generation_kw) AS renewable_generation_kw,
       SUM(net_load_kw) AS net_load_kw,
       AVG(temperature_c) AS temperature_c,
       AVG(tariff_usd_kwh) AS tariff_usd_kwh
FROM load_measurements
GROUP BY timestamp;

CREATE VIEW v_daily_facility_summary AS
SELECT facility_id,
       substr(timestamp, 1, 10) AS operating_date,
       AVG(net_load_kw) AS average_net_load_kw,
       MAX(net_load_kw) AS peak_net_load_kw,
       SUM(net_load_kw) AS energy_kwh,
       SUM(renewable_generation_kw) AS renewable_energy_kwh,
       SUM(is_anomaly) AS anomaly_count
FROM load_measurements
GROUP BY facility_id, substr(timestamp, 1, 10);
