-- ============================================================
-- Hotel Booking Analytics — Esquema normalizado (SQLite)
-- Hotel ficticio: "Hotel Aurora Bay"
-- ============================================================

PRAGMA foreign_keys = ON;

-- Elimina las tablas si ya existen (para poder re-ejecutar el script)
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS room_rates;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS room_types;
DROP TABLE IF EXISTS guests;

-- ------------------------------------------------------------
-- Huéspedes
-- ------------------------------------------------------------
CREATE TABLE guests (
    guest_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    phone           TEXT,
    country         TEXT NOT NULL,
    loyalty_tier    TEXT NOT NULL CHECK (loyalty_tier IN ('None','Silver','Gold','Platinum')),
    signup_date     TEXT NOT NULL          -- YYYY-MM-DD
);

-- ------------------------------------------------------------
-- Tipos de habitación
-- ------------------------------------------------------------
CREATE TABLE room_types (
    room_type_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    room_type_name  TEXT NOT NULL UNIQUE,   -- Standard, Deluxe, Suite, Executive
    base_rate       REAL NOT NULL,          -- tarifa de referencia (USD/noche)
    max_occupancy   INTEGER NOT NULL,
    description     TEXT
);

-- ------------------------------------------------------------
-- Habitaciones físicas del hotel
-- ------------------------------------------------------------
CREATE TABLE rooms (
    room_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number     TEXT NOT NULL UNIQUE,
    room_type_id    INTEGER NOT NULL,
    floor           INTEGER NOT NULL,
    FOREIGN KEY (room_type_id) REFERENCES room_types(room_type_id)
);

-- ------------------------------------------------------------
-- Tarifario estacional: tarifa "rack" por tipo de habitación y mes
-- ------------------------------------------------------------
CREATE TABLE room_rates (
    rate_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    room_type_id    INTEGER NOT NULL,
    month           INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    season          TEXT NOT NULL CHECK (season IN ('Low','Mid','High')),
    nightly_rate    REAL NOT NULL,
    FOREIGN KEY (room_type_id) REFERENCES room_types(room_type_id),
    UNIQUE (room_type_id, month)
);

-- ------------------------------------------------------------
-- Reservas (tabla de hechos principal)
-- ------------------------------------------------------------
CREATE TABLE reservations (
    reservation_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_id         INTEGER NOT NULL,
    room_id          INTEGER NOT NULL,
    booking_date     TEXT NOT NULL,      -- fecha en que se hizo la reserva
    check_in_date    TEXT NOT NULL,
    check_out_date   TEXT NOT NULL,
    nights           INTEGER NOT NULL,
    num_guests       INTEGER NOT NULL,
    rate_per_night   REAL NOT NULL,
    total_amount     REAL NOT NULL,
    booking_channel  TEXT NOT NULL CHECK (booking_channel IN ('Direct','OTA','Corporate','Phone')),
    status           TEXT NOT NULL CHECK (status IN ('Confirmed','CheckedOut','Cancelled','NoShow')),
    FOREIGN KEY (guest_id) REFERENCES guests(guest_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

-- ------------------------------------------------------------
-- Reseñas / satisfacción del huésped (una por estadía finalizada)
-- ------------------------------------------------------------
CREATE TABLE reviews (
    review_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id  INTEGER NOT NULL UNIQUE,
    rating          INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_date     TEXT NOT NULL,
    comment         TEXT,
    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
);

-- ------------------------------------------------------------
-- Índices para acelerar las consultas de KPIs
-- ------------------------------------------------------------
CREATE INDEX idx_reservations_checkin  ON reservations(check_in_date);
CREATE INDEX idx_reservations_checkout ON reservations(check_out_date);
CREATE INDEX idx_reservations_room     ON reservations(room_id);
CREATE INDEX idx_reservations_guest    ON reservations(guest_id);
CREATE INDEX idx_rooms_type            ON rooms(room_type_id);
CREATE INDEX idx_reviews_reservation   ON reviews(reservation_id);
