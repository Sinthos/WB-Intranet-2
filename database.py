# database.py
from models import db, Car
from sqlalchemy import or_, desc

def get_all_cars(search_term=None, sort_by='id', sort_order='asc'):
    """Retrieves all cars with optional search and sort parameters using SQLAlchemy."""
    query = Car.query

    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(or_(
            Car.listing_number.like(search_pattern),
            Car.brand.like(search_pattern),
            Car.model.like(search_pattern),
            Car.fuel_type.like(search_pattern),
            Car.transmission.like(search_pattern)
        ))

    valid_columns = {
        'id': Car.id,
        'listing_number': Car.listing_number,
        'brand': Car.brand,
        'model': Car.model,
        'price': Car.price,
        'created_at': Car.created_at
    }

    sort_column = valid_columns.get(sort_by, Car.id)

    if sort_order.lower() == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    return query.all()


def get_car_by_id(car_id):
    """Retrieves a specific car by its ID using SQLAlchemy."""
    return Car.query.get(car_id)


def insert_car(car_data):
    """Inserts a new car into the database using SQLAlchemy."""
    # Convert features list to string if it's a list
    if isinstance(car_data.get('features'), list):
        car_data['features'] = ', '.join(car_data['features'])

    new_car = Car(**car_data)
    db.session.add(new_car)
    db.session.commit()
    return new_car.id


def update_car(car_id, car_data):
    """Updates an existing car in the database using SQLAlchemy."""
    car = Car.query.get(car_id)
    if car:
        # Convert features list to string if it's a list
        if isinstance(car_data.get('features'), list):
            car_data['features'] = ', '.join(car_data['features'])
            
        for key, value in car_data.items():
            setattr(car, key, value)
        db.session.commit()
    return car


def delete_car(car_id):
    """Deletes a car from the database using SQLAlchemy."""
    car = Car.query.get(car_id)
    if car:
        db.session.delete(car)
        db.session.commit()
    return car
