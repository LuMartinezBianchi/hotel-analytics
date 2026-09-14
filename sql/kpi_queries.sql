-- ============================================================
-- Consultas SQL de KPIs hoteleros — Hotel Aurora Bay
-- (las mismas consultas se ejecutan desde python/calculate_kpis.py,
--  este archivo queda como referencia/documentación de las queries)
-- ============================================================

-- ------------------------------------------------------------
-- 1) "Explota" cada reserva en una fila por noche ocupada
--    (CTE recursiva: de check_in_date, inclusive, a check_out_date, exclusivo)
-- ------------------------------------------------------------
WITH RECURSIVE occupied_nights(reservation_id, night_date) AS (
    SELECT reservation_id, check_in_date
    FROM reservations
    WHERE status IN ('CheckedOut', 'Confirmed')

    UNION ALL

    SELECT o.reservation_id, date(o.night_date, '+1 day')
    FROM occupied_nights o
    JOIN reservations r ON r.reservation_id = o.reservation_id
    WHERE date(o.night_date, '+1 day') < r.check_out_date
)
SELECT * FROM occupied_nights LIMIT 20;

-- ------------------------------------------------------------
-- 2) Ocupación, ADR y RevPAR por mes
--    (occupied_nights + reservations + rooms para saber tarifa y tipo)
-- ------------------------------------------------------------
WITH RECURSIVE occupied_nights(reservation_id, night_date) AS (
    SELECT reservation_id, check_in_date
    FROM reservations
    WHERE status IN ('CheckedOut', 'Confirmed')
    UNION ALL
    SELECT o.reservation_id, date(o.night_date, '+1 day')
    FROM occupied_nights o
    JOIN reservations r ON r.reservation_id = o.reservation_id
    WHERE date(o.night_date, '+1 day') < r.check_out_date
),
nightly_revenue AS (
    SELECT
        strftime('%Y-%m', on_.night_date) AS year_month,
        on_.night_date,
        r.rate_per_night
    FROM occupied_nights on_
    JOIN reservations r ON r.reservation_id = on_.reservation_id
)
SELECT
    year_month,
    COUNT(*)                       AS room_nights_sold,
    ROUND(SUM(rate_per_night), 2)  AS room_revenue,
    ROUND(SUM(rate_per_night) / COUNT(*), 2) AS adr
FROM nightly_revenue
GROUP BY year_month
ORDER BY year_month;

-- ------------------------------------------------------------
-- 3) Ocupación / ADR / RevPAR / satisfacción por tipo de habitación
-- ------------------------------------------------------------
SELECT
    rt.room_type_name,
    COUNT(DISTINCT res.reservation_id)               AS reservations,
    ROUND(AVG(rv.rating), 2)                          AS avg_rating,
    COUNT(rv.review_id)                               AS review_count
FROM reservations res
JOIN rooms rm       ON rm.room_id = res.room_id
JOIN room_types rt  ON rt.room_type_id = rm.room_type_id
LEFT JOIN reviews rv ON rv.reservation_id = res.reservation_id
WHERE res.status = 'CheckedOut'
GROUP BY rt.room_type_name
ORDER BY rt.room_type_name;
