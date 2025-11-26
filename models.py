from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import json

db = SQLAlchemy()

class Car(db.Model):
    __tablename__ = 'cars'

    id = db.Column(db.Integer, primary_key=True)
    listing_number = db.Column(db.String, nullable=False, index=True)
    brand = db.Column(db.String, nullable=False, index=True)
    model = db.Column(db.String, nullable=False, index=True)
    engine_capacity = db.Column(db.Integer, nullable=False)
    power = db.Column(db.Integer, nullable=False)
    fuel_type = db.Column(db.String, nullable=False, index=True)
    transmission = db.Column(db.String, nullable=False, index=True)
    mileage = db.Column(db.Integer, nullable=False)
    first_registration = db.Column(db.String, nullable=False)
    features = db.Column(db.String, nullable=False)
    eco_badge = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False, index=True)
    vat_deductible = db.Column(db.Boolean, nullable=False)
    seller = db.Column(db.String, nullable=False, server_default='Auto Berndl', index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), index=True)
    in_stock = db.Column(db.Boolean, nullable=False, server_default='1', index=True)  # True = im Bestand, False = verkauft

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class VehicleIntake(db.Model):
    """
    Umfassendes Fahrzeug-Aufnahmeblatt mit allen Mobile.de-Feldern
    und Auto-Berndl-spezifischen Feldern.
    Struktur: 12 Hauptbereiche (A-M)
    """
    __tablename__ = 'vehicle_intakes'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    
    # ============== A. Basisdaten ==============
    brand = db.Column(db.String(100), nullable=False, index=True)  # Marke
    model_variant = db.Column(db.String(200), nullable=False)  # Modell/Variante
    first_registration = db.Column(db.String(20))  # Erstzulassung (YYYY-MM)
    vin = db.Column(db.String(17), index=True)  # Fahrgestellnummer (FIN)
    internal_number = db.Column(db.String(50), index=True)  # Fahrzeug-Nr. intern
    mileage = db.Column(db.Integer)  # Kilometerstand
    num_owners = db.Column(db.Integer)  # Anzahl Halter
    hu_au_until = db.Column(db.String(20))  # HU/AU gültig bis
    service_book = db.Column(db.String(50))  # Scheckheft: ja/nein/digital/teilweise
    accident_damage = db.Column(db.String(100))  # Unfallschaden: nein/leichter Schaden/repariert
    
    # ============== B. Motor & Antrieb ==============
    # B1 - Treibstoff (JSON Array für Mehrfachauswahl)
    fuel_types = db.Column(db.Text)  # JSON: ["Benzin", "Elektro", ...]
    
    # B2 - Leistungsdaten
    power_ps = db.Column(db.Integer)  # Leistung PS
    power_kw = db.Column(db.Integer)  # Leistung kW
    engine_capacity = db.Column(db.Integer)  # Hubraum (cm³)
    cylinders = db.Column(db.Integer)  # Zylinder
    tank_size = db.Column(db.Float)  # Tankgröße (l)
    fuel_consumption = db.Column(db.Float)  # Kraftstoffverbrauch kombiniert (l/100km)
    co2_emission = db.Column(db.Integer)  # CO₂-Ausstoß kombiniert (g/km)
    
    # B3 - Antrieb & Getriebe
    drive_type = db.Column(db.String(50))  # Antriebsart: Allrad/Front/Heck
    transmission = db.Column(db.String(50))  # Getriebe: Automatik/Halbautomatik/Schaltgetriebe
    gears = db.Column(db.Integer)  # Gänge
    
    # ============== C. Umwelt ==============
    emission_class = db.Column(db.String(50))  # Schadstoffklasse: Euro 4/5/6/6d/6d-TEMP
    eco_badge = db.Column(db.String(20))  # Umweltplakette: rot/gelb/grün
    particle_filter = db.Column(db.Boolean)  # Partikelfilter
    euro_norm = db.Column(db.String(20))  # Euronorm
    
    # ============== D. Abmessungen & Gewichte ==============
    curb_weight = db.Column(db.Integer)  # Leergewicht (kg)
    gross_weight = db.Column(db.Integer)  # Zulässiges Gesamtgewicht (kg)
    trailer_load_braked = db.Column(db.Integer)  # Anhängelast gebremst (kg)
    trailer_load_unbraked = db.Column(db.Integer)  # Anhängelast ungebremst (kg)
    support_load = db.Column(db.Integer)  # Stützlast (kg)
    
    # ============== E. Außenfarbe & Exterieur ==============
    # E1 - Farbe
    exterior_color = db.Column(db.String(50))  # Farbe
    color_metallic = db.Column(db.Boolean)  # Metallic
    color_matte = db.Column(db.Boolean)  # Matt
    color_wrapped = db.Column(db.String(100))  # Foliert (Freitext)
    
    # E2 - Exterieur-Ausstattung (JSON Array)
    exterior_features = db.Column(db.Text)  # JSON Array der ausgewählten Features
    
    # ============== F. Innenraum ==============
    # F1 - Innenfarbe
    interior_color = db.Column(db.String(50))
    
    # F2 - Material (JSON Array)
    interior_materials = db.Column(db.Text)  # JSON Array
    
    # F3 - Komfort/Sitz-Optionen (JSON Array)
    comfort_features = db.Column(db.Text)  # JSON Array
    
    # ============== G. Infotainment & Konnektivität (JSON Array) ==============
    infotainment_features = db.Column(db.Text)  # JSON Array
    
    # ============== H. Sicherheit & Assistenzsysteme (JSON Array) ==============
    safety_features = db.Column(db.Text)  # JSON Array
    airbags = db.Column(db.Text)  # JSON Array der Airbag-Typen
    
    # ============== I. Klima ==============
    climate_type = db.Column(db.String(50))  # Klimaanlage-Typ
    
    # ============== J. Parken (JSON Array) ==============
    parking_features = db.Column(db.Text)  # JSON Array
    
    # ============== K. Zustand / Service ==============
    last_inspection_date = db.Column(db.String(20))  # Letzte Inspektion Datum
    last_inspection_km = db.Column(db.Integer)  # Letzte Inspektion km
    oil_change_new = db.Column(db.Boolean)  # Ölwechsel neu
    tire_tread_front = db.Column(db.Float)  # Reifenprofiltiefe vorn (mm)
    tire_tread_rear = db.Column(db.Float)  # Reifenprofiltiefe hinten (mm)
    brakes_new = db.Column(db.Boolean)  # Bremsen neu
    timing_belt_new = db.Column(db.Boolean)  # Zahnriemen neu
    replacement_engine = db.Column(db.Boolean)  # AT-Motor
    replacement_engine_km = db.Column(db.Integer)  # AT-Motor km
    replacement_transmission = db.Column(db.Boolean)  # AT-Getriebe
    replacement_transmission_km = db.Column(db.Integer)  # AT-Getriebe km
    num_keys = db.Column(db.Integer)  # Anzahl Schlüssel
    service_book_maintained = db.Column(db.String(50))  # Scheckheft gepflegt
    warranty_type = db.Column(db.String(100))  # Garantie vorhanden
    
    # ============== L. Preise ==============
    vat_deductible = db.Column(db.Boolean)  # MwSt. ausweisbar
    net_price = db.Column(db.Float)  # Netto-Preis
    gross_price = db.Column(db.Float)  # Brutto-Preis
    transfer_costs = db.Column(db.Float)  # Überführungskosten
    optional_price = db.Column(db.Float)  # Optionaler Verkaufspreis
    
    # ============== M. Zusatzfelder ==============
    additional_notes = db.Column(db.Text)  # Freitext für weitere Ausstattung/Hinweise
    
    def to_dict(self):
        """Konvertiert das Modell in ein Dictionary."""
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            # JSON-Felder parsen
            if c.name in ['fuel_types', 'exterior_features', 'interior_materials', 
                         'comfort_features', 'infotainment_features', 'safety_features',
                         'airbags', 'parking_features']:
                if value:
                    try:
                        result[c.name] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[c.name] = []
                else:
                    result[c.name] = []
            elif isinstance(value, bool):
                result[c.name] = value
            else:
                result[c.name] = value
        return result
    
    def from_dict(self, data):
        """Aktualisiert das Modell aus einem Dictionary."""
        json_fields = ['fuel_types', 'exterior_features', 'interior_materials', 
                      'comfort_features', 'infotainment_features', 'safety_features',
                      'airbags', 'parking_features']
        
        # Numerische Felder (Integer)
        int_fields = ['mileage', 'num_owners', 'power_ps', 'power_kw', 'engine_capacity',
                     'cylinders', 'co2_emission', 'gears', 'curb_weight', 'gross_weight',
                     'trailer_load_braked', 'trailer_load_unbraked', 'support_load',
                     'last_inspection_km', 'replacement_engine_km', 'replacement_transmission_km',
                     'num_keys']
        
        # Numerische Felder (Float)
        float_fields = ['tank_size', 'fuel_consumption', 'tire_tread_front', 'tire_tread_rear',
                       'net_price', 'gross_price', 'transfer_costs', 'optional_price']
        
        # Boolean Felder
        bool_fields = ['particle_filter', 'color_metallic', 'color_matte', 'oil_change_new',
                      'brakes_new', 'timing_belt_new', 'replacement_engine', 
                      'replacement_transmission', 'vat_deductible']
        
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at']:
                if key in json_fields:
                    # JSON-Felder
                    if isinstance(value, list):
                        setattr(self, key, json.dumps(value))
                    elif isinstance(value, str):
                        setattr(self, key, value)
                elif key in int_fields:
                    # Integer-Felder: leere Strings zu None
                    if value == '' or value is None:
                        setattr(self, key, None)
                    else:
                        try:
                            setattr(self, key, int(value))
                        except (ValueError, TypeError):
                            setattr(self, key, None)
                elif key in float_fields:
                    # Float-Felder: leere Strings zu None
                    if value == '' or value is None:
                        setattr(self, key, None)
                    else:
                        try:
                            setattr(self, key, float(value))
                        except (ValueError, TypeError):
                            setattr(self, key, None)
                elif key in bool_fields:
                    # Boolean-Felder
                    if isinstance(value, bool):
                        setattr(self, key, value)
                    elif value in ['true', 'True', '1', 1]:
                        setattr(self, key, True)
                    elif value in ['false', 'False', '0', 0, '', None]:
                        setattr(self, key, False)
                    else:
                        setattr(self, key, bool(value))
                else:
                    # String-Felder: leere Strings bleiben leer oder werden zu None
                    if value == '':
                        setattr(self, key, None)
                    else:
                        setattr(self, key, value)
    
    @staticmethod
    def get_fuel_type_options():
        """Gibt alle verfügbaren Treibstoff-Optionen zurück."""
        return [
            'Benzin', 'Diesel', 'Elektro', 'Plug-in-Hybrid',
            'Hybrid (Benzin/Elektro)', 'Hybrid (Diesel/Elektro)',
            'Wasserstoff', 'Autogas (LPG)', 'Erdgas (CNG)',
            'Ethanol (E85/FFV)', 'Andere'
        ]
    
    @staticmethod
    def get_exterior_color_options():
        """Gibt alle verfügbaren Außenfarben zurück."""
        return [
            'Schwarz', 'Grau', 'Weiß', 'Silber', 'Blau', 'Rot',
            'Grün', 'Gelb', 'Orange', 'Braun', 'Beige', 'Gold',
            'Violett', 'Andere'
        ]
    
    @staticmethod
    def get_exterior_feature_options():
        """Gibt alle verfügbaren Exterieur-Ausstattungen zurück."""
        return [
            'Anhängerkupplung (fest)', 'Anhängerkupplung (abnehmbar)', 
            'Anhängerkupplung (schwenkbar)', 'Anhängerrangierassistent',
            'Panorama-Dach', 'Schiebedach', 'Faltdach', 'Dachreling',
            'Abgedunkelte Scheiben', 'Elektrische Heckklappe',
            'Leichtmetallfelgen', 'Stahlfelgen',
            'LED-Scheinwerfer', 'LED-Tagfahrlicht', 'Matrix LED', 'Laserlicht',
            'Xenon', 'Bi-Xenon', 'Nebelscheinwerfer',
            'Regensensor', 'Lichtsensor', 'Scheinwerferreinigung',
            'Reifendruckkontrolle',
            'Sommerreifen', 'Winterreifen', 'Allwetterreifen',
            'Notrad', 'Pannenkit', 'Reserverad'
        ]
    
    @staticmethod
    def get_interior_color_options():
        """Gibt alle verfügbaren Innenfarben zurück."""
        return ['Beige', 'Schwarz', 'Grau', 'Braun', 'Rot', 'Blau', 'Andere']
    
    @staticmethod
    def get_interior_material_options():
        """Gibt alle verfügbaren Innenraum-Materialien zurück."""
        return [
            'Stoff', 'Teilleder', 'Vollleder', 'Kunstleder',
            'Alcantara', 'Velours', 'Mischung / Andere'
        ]
    
    @staticmethod
    def get_comfort_feature_options():
        """Gibt alle verfügbaren Komfort-Ausstattungen zurück."""
        return [
            'Sportsitze', 'Sportpaket', 'Sportfahrwerk',
            'Elektrische Sitze', 'Elektrische Sitze mit Memory',
            'Sitzheizung', 'Sitzheizung hinten', 'Sitzbelüftung',
            'Massagesitze', 'Lordosenstütze',
            'Umklappbarer Beifahrersitz', 'Armlehne', 'Ambiente-Beleuchtung'
        ]
    
    @staticmethod
    def get_infotainment_feature_options():
        """Gibt alle verfügbaren Infotainment-Ausstattungen zurück."""
        return [
            'Navigation', 'Touchscreen', 'Digitales Cockpit',
            'Apple CarPlay', 'Android Auto', 'Bluetooth', 'USB',
            'Induktives Laden', 'Radio DAB',
            'Soundsystem (Bose)', 'Soundsystem (Harman Kardon)', 
            'Soundsystem (Burmester)', 'Soundsystem (Andere)',
            'Freisprecheinrichtung', 'TV', 'Tuner/Radio',
            'Musikstreaming integriert', 'WLAN-Hotspot', 'Sprachsteuerung'
        ]
    
    @staticmethod
    def get_safety_feature_options():
        """Gibt alle verfügbaren Sicherheits-Ausstattungen zurück."""
        return [
            'ABS', 'ESP', 'Traktionskontrolle',
            'Notbremsassistent', 'Spurhalteassistent', 'Totwinkelassistent',
            'Müdigkeitswarner', 'Abstandswarner', 'Abstandstempomat (ACC)',
            'Tempomat', 'Verkehrszeichenerkennung',
            'Ausparkassistent', 'Einparkhilfe vorne', 'Einparkhilfe hinten',
            'Rückfahrkamera', '360° Kamera', 'Selbstlenkende Systeme',
            'Nachtsichtassistent', 'Berganfahrassistent',
            'Fernlichtassistent', 'Blendfreies Fernlicht (Matrix)',
            'Keyless-Go', 'Alarmanlage', 'Isofix', 'Isofix Beifahrersitz'
        ]
    
    @staticmethod
    def get_airbag_options():
        """Gibt alle verfügbaren Airbag-Typen zurück."""
        return ['Fahrer', 'Front', 'Seiten', 'Kopf', 'Weitere']
    
    @staticmethod
    def get_climate_options():
        """Gibt alle verfügbaren Klima-Optionen zurück."""
        return [
            'Keine', 'Klimaanlage manuell', 'Klimaautomatik',
            '2-Zonen-Automatik', '3-Zonen-Automatik', '4-Zonen-Automatik'
        ]
    
    @staticmethod
    def get_parking_feature_options():
        """Gibt alle verfügbaren Park-Ausstattungen zurück."""
        return [
            'Einparkhilfe vorne', 'Einparkhilfe hinten',
            'Rückfahrkamera', '360° Kamera',
            'Selbstlenkend', 'Ausparkassistent'
        ]
    
    @staticmethod
    def get_drive_type_options():
        """Gibt alle verfügbaren Antriebsarten zurück."""
        return ['Allrad', 'Front', 'Heck']
    
    @staticmethod
    def get_transmission_options():
        """Gibt alle verfügbaren Getriebe-Typen zurück."""
        return ['Automatik', 'Halbautomatik', 'Schaltgetriebe']
    
    @staticmethod
    def get_emission_class_options():
        """Gibt alle verfügbaren Schadstoffklassen zurück."""
        return ['Euro 4', 'Euro 5', 'Euro 6', 'Euro 6d', 'Euro 6d-TEMP']
    
    @staticmethod
    def get_service_book_options():
        """Gibt alle verfügbaren Scheckheft-Optionen zurück."""
        return ['ja', 'nein', 'digital', 'teilweise']
    
    @staticmethod
    def get_accident_damage_options():
        """Gibt alle verfügbaren Unfallschaden-Optionen zurück."""
        return ['nein', 'leichter Schaden', 'repariert']
    
    @staticmethod
    def get_warranty_options():
        """Gibt alle verfügbaren Garantie-Optionen zurück."""
        return ['Keine', 'Herstellergarantie', 'Gebrauchtwagengarantie', 'Verlängerte Garantie']
