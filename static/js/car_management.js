document.addEventListener('DOMContentLoaded', function() {
    // Sortierung
    document.querySelectorAll('.sort-icon').forEach(icon => {
        icon.addEventListener('click', function() {
            const column = this.dataset.sort;
            let order = 'asc';

            if (new URLSearchParams(window.location.search).get('sort') === column) {
                order = new URLSearchParams(window.location.search).get('order') === 'asc' ? 'desc' : 'asc';
            }

            const searchParams = new URLSearchParams(window.location.search);
            searchParams.set('sort', column);
            searchParams.set('order', order);

            window.location.href = `${window.location.pathname}?${searchParams.toString()}`;
        });
    });

    // Bearbeiten
    document.querySelectorAll('.edit-car').forEach(button => {
        button.addEventListener('click', async function() {
            const carId = this.dataset.carId;
            const modal = new bootstrap.Modal(document.getElementById('editCarModal'));

            try {
                const response = await fetch(`/car/${carId}`);
                const car = await response.json();

                // Formular mit den Fahrzeugdaten füllen
                const form = document.getElementById('editCarForm');
                form.innerHTML = `
                    <input type="hidden" name="id" value="${car.id}">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label">Angebotsnummer</label>
                            <input type="text" class="form-control" name="listing_number" value="${car.listing_number}" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Marke</label>
                            <input type="text" class="form-control" name="brand" value="${car.brand}" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Modell</label>
                            <input type="text" class="form-control" name="model" value="${car.model}" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Hubraum (ccm)</label>
                            <input type="number" class="form-control" name="engine_capacity" value="${car.engine_capacity}" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Leistung</label>
                            <div class="input-group">
                                <input type="number" class="form-control" name="power" value="${car.power}" required>
                                <select class="form-select" name="power_unit" style="max-width: 100px;">
                                    <option value="ps" selected>PS</option>
                                    <option value="kw">KW</option>
                                </select>
                            </div>
                            <small class="form-text text-muted">
                                Die Leistung wird in der Datenbank in PS gespeichert.
                            </small>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Kraftstoff</label>
                            <select class="form-select" name="fuel_type" required>
                                <option value="Benzin" ${car.fuel_type === 'Benzin' ? 'selected' : ''}>Benzin</option>
                                <option value="Diesel" ${car.fuel_type === 'Diesel' ? 'selected' : ''}>Diesel</option>
                                <option value="Elektro" ${car.fuel_type === 'Elektro' ? 'selected' : ''}>Elektro</option>
                                <option value="Hybrid" ${car.fuel_type === 'Hybrid' ? 'selected' : ''}>Hybrid</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Getriebe</label>
                            <select class="form-select" name="transmission" required>
                                <option value="Automatik" ${car.transmission === 'Automatik' ? 'selected' : ''}>Automatik</option>
                                <option value="Manuell" ${car.transmission === 'Manuell' ? 'selected' : ''}>Manuell</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Kilometerstand</label>
                            <input type="number" class="form-control" name="mileage" value="${car.mileage}" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Erstzulassung</label>
                            <input type="text" class="form-control" name="first_registration" 
                                   value="${car.first_registration}" pattern="(0[1-9]|1[0-2])\/[0-9]{4}" required>
                        </div>
                        <div class="col-12">
                            <label class="form-label">Sonderausstattung</label>
                            <textarea class="form-control" name="features" rows="4" required>${car.features}</textarea>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Umweltplakette</label>
                            <select class="form-select" name="eco_badge" required>
                                <option value="1" ${car.eco_badge === 1 ? 'selected' : ''}>1 - Schwarz</option>
                                <option value="2" ${car.eco_badge === 2 ? 'selected' : ''}>2 - Rot</option>
                                <option value="3" ${car.eco_badge === 3 ? 'selected' : ''}>3 - Gelb</option>
                                <option value="4" ${car.eco_badge === 4 ? 'selected' : ''}>4 - Grün</option>
                                <option value="5" ${car.eco_badge === 5 ? 'selected' : ''}>5 - Blau</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Preis (€)</label>
                            <input type="number" class="form-control" name="price" value="${car.price}" required>
                        </div>
                        <div class="col-12">
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input" name="vat_deductible" 
                                       ${car.vat_deductible ? 'checked' : ''}>
                                <label class="form-check-label">MwSt. ausweisbar</label>
                            </div>
                        </div>
                    </div>
                `;

                setupPowerConversion(form);
                modal.show();
            } catch (error) {
                console.error('Fehler beim Laden der Fahrzeugdaten:', error);
                alert('Fehler beim Laden der Fahrzeugdaten');
            }
        });
    });

    // Setup Power Conversion
    function setupPowerConversion(form) {
        const powerInput = form.querySelector('input[name="power"]');
        const powerUnit = form.querySelector('select[name="power_unit"]');

        powerUnit.addEventListener('change', function() {
            if (!powerInput.value) return;

            const value = parseFloat(powerInput.value);
            if (this.value === 'kw') {
                // Convert PS to KW
                powerInput.value = Math.round(value / 1.359622);
            } else {
                // Convert KW to PS
                powerInput.value = Math.round(value * 1.359622);
            }
        });

        return function() {
            if (powerUnit.value === 'kw') {
                const value = parseFloat(powerInput.value);
                powerInput.value = Math.round(value * 1.359622);
            }
        };
    }

    // Speichern der Änderungen
    document.getElementById('saveCarChanges')?.addEventListener('click', async function() {
        const form = document.getElementById('editCarForm');
        const convertPower = setupPowerConversion(form);
        const carId = form.querySelector('input[name="id"]').value;

        // Konvertiere KW zu PS vor dem Speichern
        convertPower();

        // Formulardaten sammeln
        const formData = {
            listing_number: form.querySelector('input[name="listing_number"]').value,
            brand: form.querySelector('input[name="brand"]').value,
            model: form.querySelector('input[name="model"]').value,
            engine_capacity: parseInt(form.querySelector('input[name="engine_capacity"]').value),
            power: parseInt(form.querySelector('input[name="power"]').value),
            fuel_type: form.querySelector('select[name="fuel_type"]').value,
            transmission: form.querySelector('select[name="transmission"]').value,
            mileage: parseInt(form.querySelector('input[name="mileage"]').value),
            first_registration: form.querySelector('input[name="first_registration"]').value,
            features: form.querySelector('textarea[name="features"]').value,
            eco_badge: parseInt(form.querySelector('select[name="eco_badge"]').value),
            price: parseInt(form.querySelector('input[name="price"]').value),
            vat_deductible: form.querySelector('input[name="vat_deductible"]').checked
        };

        try {
            const response = await fetch(`/car/${carId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('editCarModal'));
                modal.hide();
                window.location.reload();
            } else {
                const data = await response.json();
                throw new Error(data.error || 'Fehler beim Speichern');
            }
        } catch (error) {
            console.error('Fehler beim Speichern der Änderungen:', error);
            alert('Fehler beim Speichern der Änderungen: ' + error.message);
        }
    });

    // Löschen
    document.querySelectorAll('.delete-car').forEach(button => {
        button.addEventListener('click', async function() {
            const carId = this.dataset.carId;

            if (confirm('Sind Sie sicher, dass Sie dieses Fahrzeug löschen möchten?')) {
                try {
                    const response = await fetch(`/car/${carId}`, {
                        method: 'DELETE'
                    });

                    if (response.ok) {
                        window.location.reload();
                    } else {
                        const data = await response.json();
                        throw new Error(data.error || 'Fehler beim Löschen');
                    }
                } catch (error) {
                    console.error('Fehler beim Löschen des Fahrzeugs:', error);
                    alert('Fehler beim Löschen des Fahrzeugs: ' + error.message);
                }
            }
        });
    });

    // Suchformular Reset-Button Handling
    const searchForm = document.querySelector('form[action="/view-cars"]');
    const searchInput = searchForm?.querySelector('input[name="search"]');
    const resetButton = searchForm?.querySelector('a[href="/view-cars"]');

    if (searchInput && resetButton) {
        // Zeige Reset-Button nur wenn Suchtext vorhanden
        resetButton.style.display = searchInput.value ? 'inline-block' : 'none';

        // Update Reset-Button Sichtbarkeit bei Eingabe
        searchInput.addEventListener('input', function() {
            resetButton.style.display = this.value ? 'inline-block' : 'none';
        });
    }

    // Fehlermeldungen für Formulareingaben
    const editForm = document.getElementById('editCarForm');
    if (editForm) {
        const inputs = editForm.querySelectorAll('input[required], select[required], textarea[required]');
        inputs.forEach(input => {
            input.addEventListener('invalid', function(e) {
                e.preventDefault();
                this.classList.add('is-invalid');
            });

            input.addEventListener('input', function() {
                if (this.validity.valid) {
                    this.classList.remove('is-invalid');
                }
            });
        });
    }
});