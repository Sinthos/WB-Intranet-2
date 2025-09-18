from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class CarForm(FlaskForm):
    listing_number = StringField('Angebotsnummer', validators=[DataRequired(), Length(min=1, max=100)])
    brand = StringField('Marke', validators=[DataRequired(), Length(min=1, max=100)])
    model = StringField('Modell', validators=[DataRequired(), Length(min=1, max=100)])
    engine_capacity = IntegerField('Hubraum (ccm)', validators=[DataRequired(), NumberRange(min=0)])
    power = IntegerField('Leistung (PS)', validators=[DataRequired(), NumberRange(min=0)])
    fuel_type = SelectField('Kraftstoffart', choices=[
        ('Benzin', 'Benzin'),
        ('Diesel', 'Diesel'),
        ('Elektro', 'Elektro'),
        ('Hybrid', 'Hybrid')
    ], validators=[DataRequired()])
    transmission = SelectField('Getriebe', choices=[
        ('Manuell', 'Manuell'),
        ('Automatik', 'Automatik')
    ], validators=[DataRequired()])
    mileage = IntegerField('Kilometerstand', validators=[DataRequired(), NumberRange(min=0)])
    first_registration = StringField('Erstzulassung (MM/JJJJ)', validators=[DataRequired()])
    features = TextAreaField('Ausstattung (eine pro Zeile)', validators=[DataRequired()])
    eco_badge = SelectField('Umweltplakette', choices=[
        (4, '4 (Grün)'),
        (3, '3 (Gelb)'),
        (2, '2 (Rot)'),
        (1, '1 (Keine)')
    ], coerce=int, validators=[DataRequired()])
    price = IntegerField('Preis (€)', validators=[DataRequired(), NumberRange(min=0)])
    vat_deductible = BooleanField('MwSt. ausweisbar')
    submit = SubmitField('PDF generieren und Speichern')
