# database.py
import sqlite3
import os
from datetime import datetime

# Definiere einen Standard-Datenbankpfad relativ zum Projektverzeichnis
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'data', 'car_data.db')

# Hole Datenbankpfad aus Umgebungsvariable oder nutze Standard
DATABASE = os.getenv('DATABASE_PATH', DEFAULT_DB_PATH)


def get_db_connection():
    """Creates a database connection and returns it"""
    # Stelle sicher, dass das Verzeichnis existiert
    db_dir = os.path.dirname(DATABASE)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the SQLite database and creates the 'cars' table if it does not exist."""
    # Stelle sicher, dass der data Ordner existiert
    data_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_number TEXT NOT NULL,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                engine_capacity INTEGER NOT NULL,
                power INTEGER NOT NULL,
                fuel_type TEXT NOT NULL,
                transmission TEXT NOT NULL,
                mileage INTEGER NOT NULL,
                first_registration TEXT NOT NULL,
                features TEXT NOT NULL,
                eco_badge INTEGER NOT NULL,
                price INTEGER NOT NULL,
                vat_deductible BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


def get_all_cars(search_term=None, sort_by='id', sort_order='asc'):
    """Retrieves all cars with optional search and sort parameters"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = 'SELECT * FROM cars'
        params = []

        if search_term:
            query += ''' WHERE 
                listing_number LIKE ? OR 
                brand LIKE ? OR 
                model LIKE ? OR 
                fuel_type LIKE ? OR
                transmission LIKE ?
            '''
            search_pattern = f'%{search_term}%'
            params.extend([search_pattern] * 5)

        valid_columns = ['id', 'listing_number', 'brand', 'model', 'price', 'created_at']
        if sort_by in valid_columns:
            query += f' ORDER BY {sort_by}'
            if sort_order.lower() == 'desc':
                query += ' DESC'
            else:
                query += ' ASC'

        cursor.execute(query, params)
        return cursor.fetchall()


def get_car_by_id(car_id):
    """Retrieves a specific car by its ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cars WHERE id = ?', (car_id,))
        return cursor.fetchone()


def insert_car(car_data):
    """Fügt ein neues Fahrzeug in die Datenbank ein."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cars (
                listing_number, brand, model, engine_capacity,
                power, fuel_type, transmission, mileage,
                first_registration, features, eco_badge, price,
                vat_deductible
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            car_data['listing_number'],
            car_data['brand'],
            car_data['model'],
            car_data['engine_capacity'],
            car_data['power'],
            car_data['fuel_type'],
            car_data['transmission'],
            car_data['mileage'],
            car_data['first_registration'],
            ', '.join(car_data['features']) if isinstance(car_data['features'], list) else car_data['features'],
            car_data['eco_badge'],
            car_data['price'],
            car_data['vat_deductible']
        ))
        conn.commit()
        return cursor.lastrowid


def update_car(car_id, car_data):
    """Updates an existing car in the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE cars 
            SET listing_number=?, brand=?, model=?, engine_capacity=?,
                power=?, fuel_type=?, transmission=?, mileage=?,
                first_registration=?, features=?, eco_badge=?, price=?,
                vat_deductible=?
            WHERE id=?
        ''', (
            car_data['listing_number'], car_data['brand'], car_data['model'],
            car_data['engine_capacity'], car_data['power'], car_data['fuel_type'],
            car_data['transmission'], car_data['mileage'], car_data['first_registration'],
            car_data['features'], car_data['eco_badge'], car_data['price'],
            car_data['vat_deductible'], car_id
        ))
        conn.commit()


def delete_car(car_id):
    """Deletes a car from the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cars WHERE id = ?', (car_id,))
        conn.commit()