-- One row per measured hour. Include zero readings.
SELECT room_id,COUNT(*) AS measured_hours,SUM(wh) AS recorded_wh
FROM readings GROUP BY room_id;

-- Days with all 24 readings in every room.
WITH daily AS (
    SELECT room_id,date(hour_start) AS day,COUNT(*) AS measured
    FROM readings GROUP BY room_id,day
)
SELECT day FROM daily GROUP BY day HAVING COUNT(*)=3 AND MIN(measured)=24;

-- Complete whole-house hours and ties.
WITH complete AS (
    SELECT hour_start,SUM(wh) AS total_wh
    FROM readings GROUP BY hour_start HAVING COUNT(*)=3
)
SELECT *,DENSE_RANK() OVER(ORDER BY total_wh DESC) AS peak_rank
FROM complete ORDER BY peak_rank,hour_start;
