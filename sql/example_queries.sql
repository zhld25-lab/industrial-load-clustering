-- 1. Confirm that the database is synthetic before analysis.
SELECT value AS disclosure
FROM dataset_metadata
WHERE key = 'data_notice';

-- 2. Find the park-wide synthetic peak.
SELECT timestamp, net_load_kw
FROM v_park_hourly_load
ORDER BY net_load_kw DESC
LIMIT 10;

-- 3. Compare average load by fictional facility type.
SELECT
    f.facility_type,
    ROUND(AVG(m.net_load_kw), 2) AS average_net_load_kw,
    ROUND(MAX(m.net_load_kw), 2) AS peak_net_load_kw,
    ROUND(SUM(m.renewable_generation_kw), 2) AS renewable_energy_kwh
FROM load_measurements AS m
JOIN facilities AS f USING (facility_id)
WHERE m.quality_flag <> 'missing'
GROUP BY f.facility_type
ORDER BY peak_net_load_kw DESC;

-- 4. Data-quality summary.
SELECT quality_flag, COUNT(*) AS record_count
FROM load_measurements
GROUP BY quality_flag;
