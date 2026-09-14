"""
generate_data.py
-----------------
Genera datos de muestra realistas para el Hotel Aurora Bay (hotel ficticio)
y los carga en una base SQLite (data/hotel.db) que respeta el esquema
definido en sql/schema.sql.

Uso:
    python generate_data.py

Requiere: faker (pip install faker)
"""

import sqlite3
import random
from datetime import date, timedelta
from faker import Faker

# ------------------------------------------------------------------
# Configuración general
# ------------------------------------------------------------------
random.seed(42)               # reproducibilidad: mismos datos cada vez que se corre
fake = Faker()
Faker.seed(42)

DB_PATH = "data/hotel.db"
SCHEMA_PATH = "sql/schema.sql"

NUM_GUESTS = 900
START_DATE = date(2024, 1, 1)
END_DATE = date(2025, 12, 31)          # 2 años de historia
TODAY = date(2025, 12, 31)             # "hoy" ficticio para el dataset

ROOM_TYPES = [
    # nombre,      tarifa base, ocupación máx, descripción
    ("Standard",   85.0,  2, "Habitación doble estándar"),
    ("Deluxe",    130.0,  2, "Habitación superior con vista"),
    ("Suite",     220.0,  3, "Suite junior con living"),
    ("Executive", 360.0,  4, "Suite ejecutiva de dos ambientes"),
]

# Cantidad de habitaciones físicas por tipo (total = 60)
ROOMS_PER_TYPE = {
    "Standard": 26,
    "Deluxe": 20,
    "Suite": 10,
    "Executive": 4,
}

CHANNELS = ["Direct", "OTA", "Corporate", "Phone"]
CHANNEL_WEIGHTS = [0.30, 0.45, 0.15, 0.10]

LOYALTY_TIERS = ["None", "Silver", "Gold", "Platinum"]
LOYALTY_WEIGHTS = [0.55, 0.25, 0.15, 0.05]

# Meses de temporada alta / media / baja
HIGH_SEASON_MONTHS = {1, 2, 12}
MID_SEASON_MONTHS = {3, 4, 10, 11}
LOW_SEASON_MONTHS = {5, 6, 7, 8, 9}


def season_for_month(month: int) -> str:
    if month in HIGH_SEASON_MONTHS:
        return "High"
    if month in MID_SEASON_MONTHS:
        return "Mid"
    return "Low"


SEASON_MULTIPLIER = {"Low": 0.85, "Mid": 1.0, "High": 1.45}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def daterange(start: date, end: date):
    for n in range((end - start).days + 1):
        yield start + timedelta(days=n)


def build_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


# ------------------------------------------------------------------
# Carga de tablas de referencia
# ------------------------------------------------------------------
def insert_room_types(cur):
    for name, base_rate, max_occ, desc in ROOM_TYPES:
        cur.execute(
            "INSERT INTO room_types (room_type_name, base_rate, max_occupancy, description) "
            "VALUES (?, ?, ?, ?)",
            (name, base_rate, max_occ, desc),
        )
    return {name: i + 1 for i, (name, *_rest) in enumerate(ROOM_TYPES)}


def insert_room_rates(cur, type_ids):
    base_rate_by_type = {name: base for name, base, *_ in ROOM_TYPES}
    for name, type_id in type_ids.items():
        base = base_rate_by_type[name]
        for month in range(1, 13):
            season = season_for_month(month)
            rate = round(base * SEASON_MULTIPLIER[season], 2)
            cur.execute(
                "INSERT INTO room_rates (room_type_id, month, season, nightly_rate) "
                "VALUES (?, ?, ?, ?)",
                (type_id, month, season, rate),
            )


def insert_rooms(cur, type_ids):
    room_ids_by_type = {name: [] for name in type_ids}
    room_number = 100
    floor = 1
    rooms_on_floor = 0
    for name, count in ROOMS_PER_TYPE.items():
        type_id = type_ids[name]
        for _ in range(count):
            room_number += 1
            rooms_on_floor += 1
            if rooms_on_floor > 12:          # 12 habitaciones por piso
                floor += 1
                rooms_on_floor = 1
            cur.execute(
                "INSERT INTO rooms (room_number, room_type_id, floor) VALUES (?, ?, ?)",
                (str(room_number), type_id, floor),
            )
            room_ids_by_type[name].append(cur.lastrowid)
    return room_ids_by_type


def insert_guests(cur):
    guest_ids = []
    seen_emails = set()
    for _ in range(NUM_GUESTS):
        first = fake.first_name()
        last = fake.last_name()
        email = fake.unique.email()
        phone = fake.phone_number()
        country = fake.country()
        tier = random.choices(LOYALTY_TIERS, weights=LOYALTY_WEIGHTS)[0]
        signup = fake.date_between(start_date="-4y", end_date="-1d")
        cur.execute(
            "INSERT INTO guests (first_name, last_name, email, phone, country, "
            "loyalty_tier, signup_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (first, last, email, phone, country, tier, signup.isoformat()),
        )
        guest_ids.append(cur.lastrowid)
    return guest_ids


# ------------------------------------------------------------------
# Motor de reservas: evita doble reserva de una misma habitación
# ------------------------------------------------------------------
def generate_reservations(cur, guest_ids, room_ids_by_type, rate_lookup):
    """
    rate_lookup: dict {(room_type_name, month): nightly_rate}
    """
    all_types = list(ROOMS_PER_TYPE.keys())
    type_weights = [0.42, 0.33, 0.18, 0.07]  # demanda relativa Standard/Deluxe/Suite/Executive

    # calendario de ocupación por habitación: room_id -> set(fechas ocupadas)
    booked_dates = {rid: set() for ids in room_ids_by_type.values() for rid in ids}

    reservation_rows = []
    reservation_id = 0

    for day in daterange(START_DATE, END_DATE):
        weekday = day.weekday()  # 0=lunes ... 6=domingo
        season = season_for_month(day.month)

        # % objetivo de nuevos check-ins ese día (fin de semana y temporada alta suben demanda)
        base_target = 0.46
        if weekday in (4, 5):          # viernes y sábado
            base_target += 0.10
        if season == "High":
            base_target += 0.10
        elif season == "Low":
            base_target -= 0.09

        total_rooms = sum(len(v) for v in room_ids_by_type.values())
        target_checkins = max(1, int(total_rooms * base_target * random.uniform(0.7, 1.3)))

        for _ in range(target_checkins):
            room_type = random.choices(all_types, weights=type_weights)[0]
            room_id = random.choice(room_ids_by_type[room_type])

            nights = random.choices([1, 2, 3, 4, 5, 7], weights=[0.20, 0.30, 0.22, 0.14, 0.09, 0.05])[0]
            checkout = day + timedelta(days=nights)

            # chequear disponibilidad de la habitación en todo el rango
            stay_range = {day + timedelta(days=n) for n in range(nights)}
            if stay_range & booked_dates[room_id]:
                continue  # habitación ocupada, se pierde este intento (realista: hotel lleno)

            booked_dates[room_id].update(stay_range)

            guest_id = random.choice(guest_ids)
            lead_time = random.randint(0, 90)
            booking_date = day - timedelta(days=lead_time)
            if booking_date < START_DATE - timedelta(days=180):
                booking_date = day

            base_rate = rate_lookup[(room_type, day.month)]
            discount = random.uniform(-0.08, 0.03)  # pequeñas variaciones/descuentos
            rate_per_night = round(base_rate * (1 + discount), 2)
            total_amount = round(rate_per_night * nights, 2)
            num_guests = random.randint(1, {"Standard": 2, "Deluxe": 2, "Suite": 3, "Executive": 4}[room_type])
            channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]

            if checkout <= TODAY:
                status = random.choices(
                    ["CheckedOut", "Cancelled", "NoShow"], weights=[0.90, 0.07, 0.03]
                )[0]
            else:
                status = random.choices(["Confirmed", "Cancelled"], weights=[0.9, 0.1])[0]

            reservation_id += 1
            reservation_rows.append(
                (
                    reservation_id, guest_id, room_id, booking_date.isoformat(),
                    day.isoformat(), checkout.isoformat(), nights, num_guests,
                    rate_per_night, total_amount, channel, status,
                )
            )

    cur.executemany(
        "INSERT INTO reservations (reservation_id, guest_id, room_id, booking_date, "
        "check_in_date, check_out_date, nights, num_guests, rate_per_night, "
        "total_amount, booking_channel, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        reservation_rows,
    )
    return reservation_rows


# ------------------------------------------------------------------
# Reseñas de satisfacción (solo para estadías finalizadas -> CheckedOut)
# ------------------------------------------------------------------
POSITIVE_COMMENTS = [
    "Excelente atención del personal, volveríamos sin dudarlo.",
    "Habitación impecable y muy cómoda.",
    "Desayuno espectacular y buena ubicación.",
    "Todo perfecto, superó nuestras expectativas.",
]
NEUTRAL_COMMENTS = [
    "Estadía correcta, sin grandes sorpresas.",
    "Buena relación precio-calidad.",
    "Cumplió con lo esperado.",
]
NEGATIVE_COMMENTS = [
    "El check-in demoró demasiado.",
    "La habitación necesitaba mantenimiento.",
    "Esperaba más por el precio pagado.",
]


def insert_reviews(cur, reservation_rows):
    # columnas: 0 reservation_id, 5 check_out_date, 11 status
    checked_out = [r for r in reservation_rows if r[11] == "CheckedOut"]
    review_id = 0
    rows = []
    for r in checked_out:
        if random.random() > 0.62:   # no todas las estadías dejan reseña
            continue
        reservation_id = r[0]
        checkout_date = date.fromisoformat(r[5])
        rating = random.choices([5, 4, 3, 2, 1], weights=[0.38, 0.32, 0.16, 0.09, 0.05])[0]
        review_date = checkout_date + timedelta(days=random.randint(0, 5))
        if rating >= 4:
            comment = random.choice(POSITIVE_COMMENTS)
        elif rating == 3:
            comment = random.choice(NEUTRAL_COMMENTS)
        else:
            comment = random.choice(NEGATIVE_COMMENTS)
        review_id += 1
        rows.append((reservation_id, rating, review_date.isoformat(), comment))

    cur.executemany(
        "INSERT INTO reviews (reservation_id, rating, review_date, comment) VALUES (?,?,?,?)",
        rows,
    )
    return len(rows)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    conn = sqlite3.connect(DB_PATH)
    build_schema(conn)
    cur = conn.cursor()

    print("Insertando tipos de habitación...")
    type_ids = insert_room_types(cur)

    print("Insertando tarifario estacional (room_rates)...")
    insert_room_rates(cur, type_ids)

    print("Insertando habitaciones físicas...")
    room_ids_by_type = insert_rooms(cur, type_ids)

    print(f"Insertando {NUM_GUESTS} huéspedes...")
    guest_ids = insert_guests(cur)

    # lookup rápido de tarifa por (tipo, mes)
    cur.execute("SELECT room_type_name, month, nightly_rate FROM room_rates rr "
                "JOIN room_types rt ON rt.room_type_id = rr.room_type_id")
    rate_lookup = {(name, month): rate for name, month, rate in cur.fetchall()}

    print("Generando reservas (esto puede tardar unos segundos)...")
    reservation_rows = generate_reservations(cur, guest_ids, room_ids_by_type, rate_lookup)
    print(f"  -> {len(reservation_rows)} reservas generadas")

    print("Generando reseñas de satisfacción...")
    n_reviews = insert_reviews(cur, reservation_rows)
    print(f"  -> {n_reviews} reseñas generadas")

    conn.commit()
    conn.close()
    print(f"\nListo. Base de datos creada en {DB_PATH}")


if __name__ == "__main__":
    main()
