"""
export_data.py
----------------
Exporta las tablas de data/hotel.db a CSV:
tablas dimensionales (dim_*), la tabla de hechos de reservas y reseñas
(fact_*), y una tabla de calendario (dim_date) para el modelo de Power BI.
"""

import sqlite3
from datetime import date, timedelta

import pandas as pd

DB_PATH = "data/hotel.db"
OUT_DIR = "data"

START_DATE = date(2024, 1, 1)
END_DATE = date(2025, 12, 31)


def export_dimension_and_fact_tables(conn):

    dim_guests = pd.read_sql(
        "SELECT guest_id, first_name, last_name, email, country, loyalty_tier, signup_date "
        "FROM guests", conn,
    )
    dim_guests.to_csv(f"{OUT_DIR}/dim_guests.csv", index=False)

    dim_room_types = pd.read_sql(
        "SELECT room_type_id, room_type_name, base_rate, max_occupancy, description "
        "FROM room_types", conn,
    )
    dim_room_types.to_csv(f"{OUT_DIR}/dim_room_types.csv", index=False)

    dim_rooms = pd.read_sql(
        """
        SELECT rm.room_id, rm.room_number, rm.floor, rt.room_type_name
        FROM rooms rm
        JOIN room_types rt ON rt.room_type_id = rm.room_type_id
        """,
        conn,
    )
    dim_rooms.to_csv(f"{OUT_DIR}/dim_rooms.csv", index=False)

    fact_reservations = pd.read_sql(
        """
        SELECT
            res.reservation_id, res.guest_id, res.room_id, rt.room_type_name,
            res.booking_date, res.check_in_date, res.check_out_date, res.nights,
            res.num_guests, res.rate_per_night, res.total_amount,
            res.booking_channel, res.status
        FROM reservations res
        JOIN rooms rm      ON rm.room_id = res.room_id
        JOIN room_types rt ON rt.room_type_id = rm.room_type_id
        """,
        conn,
    )
    fact_reservations.to_csv(f"{OUT_DIR}/fact_reservations.csv", index=False)

    fact_reviews = pd.read_sql(
        """
        SELECT
            rv.review_id, rv.reservation_id, rt.room_type_name,
            rv.rating, rv.review_date, rv.comment
        FROM reviews rv
        JOIN reservations res ON res.reservation_id = rv.reservation_id
        JOIN rooms rm          ON rm.room_id = res.room_id
        JOIN room_types rt     ON rt.room_type_id = rm.room_type_id
        """,
        conn,
    )
    fact_reviews.to_csv(f"{OUT_DIR}/fact_reviews.csv", index=False)

    return fact_reservations, dim_guests, dim_rooms


def export_dim_date():
    rows = []
    d = START_DATE
    while d <= END_DATE:
        month = d.month
        if month in (1, 2, 12):
            season = "High"
        elif month in (3, 4, 10, 11):
            season = "Mid"
        else:
            season = "Low"
        rows.append(
            {
                "date": d.isoformat(),
                "year": d.year,
                "month": d.month,
                "month_name": d.strftime("%B"),
                "day": d.day,
                "day_of_week": d.weekday(),          # 0=lunes
                "day_name": d.strftime("%A"),
                "is_weekend": d.weekday() in (4, 5),  # viernes/sábado (check-ins pico)
                "season": season,
            }
        )
        d += timedelta(days=1)
    pd.DataFrame(rows).to_csv(f"{OUT_DIR}/dim_date.csv", index=False)


def main():
    conn = sqlite3.connect(DB_PATH)

    fact_reservations, dim_guests, dim_rooms = export_dimension_and_fact_tables(conn)
    export_dim_date()

    conn.close()

    print(f"\n{len(dim_guests)} huéspedes, {len(dim_rooms)} habitaciones, "
          f"{len(fact_reservations)} reservas exportadas.")


if __name__ == "__main__":
    main()
