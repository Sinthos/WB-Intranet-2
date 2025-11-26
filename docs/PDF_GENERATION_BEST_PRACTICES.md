# PDF-Generierung mit WeasyPrint - Best Practices

## Übersicht

Dieses Dokument beschreibt die Best Practices für die PDF-Generierung mit WeasyPrint in diesem Projekt. Es dient als Referenz für zukünftige Entwicklungen und soll verhindern, dass durch CSS-Änderungen das PDF-Layout beschädigt wird.

**Wichtig:** WeasyPrint ist KEINE Browser-Engine. Es interpretiert HTML/CSS anders als Chrome, Firefox oder Safari. Was im Browser funktioniert, kann in WeasyPrint komplett anders aussehen oder gar nicht funktionieren.

---

## Inhaltsverzeichnis

1. [Grundlegende Architektur](#grundlegende-architektur)
2. [CSS-Regeln für @page](#css-regeln-für-page)
3. [Layout-Strategien](#layout-strategien)
4. [Was funktioniert](#was-funktioniert)
5. [Was NICHT funktioniert](#was-nicht-funktioniert)
6. [Bilder und Assets](#bilder-und-assets)
7. [Farben und Druckausgabe](#farben-und-druckausgabe)
8. [Debugging-Tipps](#debugging-tipps)
9. [Häufige Fehler und Lösungen](#häufige-fehler-und-lösungen)
10. [Code-Beispiele](#code-beispiele)

---

## Grundlegende Architektur

### Wie WeasyPrint funktioniert

```
HTML-Template → Jinja2-Rendering → HTML-String → WeasyPrint → PDF
```

WeasyPrint verwendet:
- **Cairo** für das Rendering
- **Pango** für Text-Layout
- **GDK-PixBuf** für Bilder
- Eigene CSS-Engine (NICHT Blink/Gecko/WebKit)

### Unsere Implementierung

```python
# routes/view_routes.py
from weasyprint import HTML
from io import BytesIO

def generate_pdf_from_template(html_content):
    """Helper function to generate PDF with correct image handling"""
    pdf_file = BytesIO()
    html = HTML(string=html_content, base_url=request.url_root)
    html.write_pdf(pdf_file, presentational_hints=True)
    pdf_file.seek(0)
    return pdf_file
```

**Wichtige Parameter:**
- `base_url`: Ermöglicht das Laden von relativen Ressourcen (Bilder, CSS)
- `presentational_hints=True`: Berücksichtigt HTML-Attribute wie `width`, `height`

---

## CSS-Regeln für @page

### Korrekte @page-Definition

```css
@page {
  size: A4;           /* Oder: A4 portrait, A4 landscape, letter */
  margin: 0;          /* Wir kontrollieren Margins selbst im .page-Container */
}
```

### Warum `margin: 0`?

Wenn wir `margin` in `@page` setzen, wird der verfügbare Bereich für den Inhalt reduziert. Es ist einfacher, die Margins im HTML-Container zu kontrollieren:

```css
.page {
  width: 190mm;       /* 210mm - 20mm für Seitenränder */
  min-height: 297mm;  /* A4 Höhe */
  margin: 0 auto;     /* Zentriert auf der Seite */
  padding: 10px;      /* Innenabstand */
}
```

### Seitengrößen-Referenz

| Format | Breite | Höhe |
|--------|--------|------|
| A4 | 210mm | 297mm |
| A5 | 148mm | 210mm |
| Letter | 216mm | 279mm |
| Legal | 216mm | 356mm |

---

## Layout-Strategien

### ✅ EMPFOHLEN: Lineares Flow-Layout

```css
.page {
  position: relative;
  width: 190mm;
  min-height: 297mm;    /* WICHTIG: min-height, NICHT height */
  margin: 0 auto;
  padding: 10px;
  background: white;
}

/* Elemente fließen natürlich von oben nach unten */
.header { /* ... */ }
.content { /* ... */ }
.footer { /* ... */ }
```

**Warum `min-height` statt `height`?**
- `height: 297mm` erzwingt eine feste Höhe, auch wenn der Inhalt weniger Platz braucht
- `min-height: 297mm` erlaubt dem Inhalt zu wachsen, falls nötig
- Bei Überlauf wird automatisch eine neue Seite erstellt

### ⚠️ VORSICHT: Flexbox

Flexbox funktioniert in WeasyPrint, aber mit Einschränkungen:

```css
/* ✅ OK: Einfache horizontale Anordnung */
.row {
  display: flex;
  gap: 20px;
}

/* ❌ PROBLEMATISCH: Komplexe Flex-Layouts */
.page {
  display: flex;
  flex-direction: column;
  height: 297mm;
  justify-content: space-between;  /* Funktioniert nicht zuverlässig */
}
```

### ❌ VERMEIDEN: CSS Grid für Hauptlayout

CSS Grid wird von WeasyPrint unterstützt, aber komplexe Grid-Layouts können unerwartete Ergebnisse liefern:

```css
/* ❌ NICHT für Seitenlayout verwenden */
.page {
  display: grid;
  grid-template-rows: auto 1fr auto;
}

/* ✅ OK für kleine Bereiche */
.price-section {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 15px;
}
```

---

## Was funktioniert

### ✅ Zuverlässig unterstützt

| Feature | Beispiel | Hinweise |
|---------|----------|----------|
| Block-Layout | `display: block` | Standard, immer verwenden |
| Inline-Block | `display: inline-block` | Für horizontale Anordnung |
| Floats | `float: left/right` | Klassisch, aber funktioniert |
| Einfache Flexbox | `display: flex` | Nur für einfache Fälle |
| Tabellen | `<table>` oder `display: table` | Sehr zuverlässig |
| Absolute Positionierung | `position: absolute` | Innerhalb von `position: relative` |
| Borders | `border: 1px solid #000` | Vollständig unterstützt |
| Border-Radius | `border-radius: 8px` | Funktioniert |
| Box-Shadow | `box-shadow: 0 2px 4px rgba(0,0,0,0.1)` | Funktioniert |
| Hintergrundfarben | `background-color: #f8f9fa` | Mit print-color-adjust |
| SVG | Inline SVG | Vollständig unterstützt |
| Web-Fonts | `@font-face` | Mit korrektem Pfad |

### ✅ Beispiel: Zwei-Spalten-Layout

```css
.content-container {
  display: flex;
  gap: 30px;
  margin-bottom: 15px;
  justify-content: space-between;
}

.left-column, .right-column {
  flex: 0 0 49%;           /* Feste Breite, kein Wachsen/Schrumpfen */
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  min-height: 480px;       /* min-height, nicht height */
  display: flex;
  flex-direction: column;
}
```

---

## Was NICHT funktioniert

### ❌ Problematische CSS-Features

| Feature | Problem | Alternative |
|---------|---------|-------------|
| `height: 100%` auf .page | Ignoriert oder falsch berechnet | `min-height: 297mm` |
| `margin-top: auto` für Footer | Funktioniert nicht in Flex-Container | Feste Margins oder natürlicher Flow |
| `flex-grow: 1` für Hauptinhalt | Unzuverlässig | Feste oder min-heights |
| `position: fixed` | Wird wie `absolute` behandelt | `position: absolute` |
| `overflow: hidden` mit fester Höhe | Schneidet Inhalt ab | Vermeiden |
| `calc()` mit komplexen Werten | Manchmal falsch berechnet | Feste Werte |
| `vh/vw` Einheiten | Nicht unterstützt | `mm`, `cm`, `px` |
| CSS Variables (Custom Properties) | Eingeschränkt | Direkte Werte |
| `@media screen` | Wird ignoriert | `@media print` |

### ❌ Beispiel: Was NICHT tun

```css
/* ❌ FALSCH: Versucht Footer nach unten zu drücken */
.page {
  display: flex;
  flex-direction: column;
  height: 297mm;
}

.content {
  flex-grow: 1;  /* Soll den Platz füllen - funktioniert NICHT */
}

.footer {
  margin-top: auto;  /* Soll Footer nach unten drücken - funktioniert NICHT */
}
```

```css
/* ✅ RICHTIG: Natürlicher Flow */
.page {
  position: relative;
  min-height: 297mm;
}

.content {
  /* Kein flex-grow nötig */
}

.footer {
  margin-top: 30px;  /* Fester Abstand */
}
```

---

## Bilder und Assets

### Bildpfade

```html
<!-- ✅ RICHTIG: url_for mit base_url -->
<img src="{{ url_for('static', filename='images/logo.png') }}" alt="Logo">

<!-- ❌ FALSCH: Relativer Pfad ohne base_url -->
<img src="/static/images/logo.png" alt="Logo">
```

**Wichtig:** Der `base_url` Parameter in WeasyPrint muss gesetzt sein:

```python
html = HTML(string=html_content, base_url=request.url_root)
```

### Bildgrößen

```css
.logo {
  width: 250px;      /* Feste Breite */
  height: auto;      /* Proportional */
  display: block;    /* Verhindert Inline-Spacing */
}

img {
  max-width: 100%;   /* Verhindert Überlauf */
}
```

### Print-Color-Adjust für Bilder

```css
img {
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
  display: block !important;
  visibility: visible !important;
}
```

---

## Farben und Druckausgabe

### Hintergrundfarben im Druck

Standardmäßig werden Hintergrundfarben beim Drucken entfernt. Um sie zu erhalten:

```css
.colored-box {
  background-color: #e4002b;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
  color-adjust: exact !important;
}
```

### @media print

```css
@media print {
  /* Diese Regeln gelten nur für den Druck/PDF */
  .no-print {
    display: none !important;
  }
  
  .print-only {
    display: block !important;
  }
  
  /* Farben erzwingen */
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
```

---

## Debugging-Tipps

### 1. HTML im Browser testen

Öffne das gerenderte HTML direkt im Browser, um das Layout zu prüfen:

```python
# Temporär zum Debuggen
@app.route('/debug-pdf/<int:car_id>')
def debug_pdf(car_id):
    car = get_car_by_id(car_id)
    car_dict = car.to_dict()
    car_dict['features'] = car_dict['features'].split(', ')
    return render_template('car_template.html', car=car_dict, ...)
```

### 2. PDF-Ausgabe prüfen

```python
# Speichere PDF temporär zur Inspektion
html.write_pdf('/tmp/debug.pdf')
```

### 3. WeasyPrint-Logging aktivieren

```python
import logging
logging.getLogger('weasyprint').setLevel(logging.DEBUG)
```

### 4. Schrittweise Änderungen

**NIEMALS** mehrere CSS-Änderungen gleichzeitig machen. Immer:
1. Eine Änderung machen
2. PDF generieren und prüfen
3. Nächste Änderung

---

## Häufige Fehler und Lösungen

### Problem: Footer auf zweiter Seite

**Ursache:** Inhalt zu lang für eine Seite

**Lösungen:**
1. Schriftgrößen reduzieren
2. Abstände (padding/margin) reduzieren
3. Weniger Inhalt pro Seite
4. `min-height` der Spalten reduzieren

```css
/* Vorher */
.left-column, .right-column {
  min-height: 480px;
}

/* Nachher - wenn nötig */
.left-column, .right-column {
  min-height: 400px;
}
```

### Problem: Bilder werden nicht angezeigt

**Ursache:** Falscher Pfad oder fehlender base_url

**Lösung:**
```python
html = HTML(string=html_content, base_url=request.url_root)
```

### Problem: Hintergrundfarben fehlen

**Ursache:** print-color-adjust nicht gesetzt

**Lösung:**
```css
.element {
  background-color: #f00;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
```

### Problem: Text wird abgeschnitten

**Ursache:** `overflow: hidden` mit fester Höhe

**Lösung:** `overflow: hidden` entfernen oder `min-height` statt `height` verwenden

### Problem: Flexbox-Layout bricht

**Ursache:** Komplexe Flex-Eigenschaften

**Lösung:** Vereinfachen oder auf Block-Layout umstellen

---

## Code-Beispiele

### Vollständiges Template-Grundgerüst

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>PDF Dokument</title>
  <style>
    @page {
      size: A4;
      margin: 0;
    }
    
    * {
      box-sizing: border-box;
    }
    
    body {
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      background: white;
    }
    
    .page {
      position: relative;
      width: 190mm;
      min-height: 297mm;
      margin: 0 auto;
      padding: 10mm;
      background: white;
    }
    
    /* Header */
    .header {
      margin-bottom: 10mm;
      padding-bottom: 5mm;
      border-bottom: 1px solid #ccc;
    }
    
    /* Hauptinhalt */
    .content {
      /* Natürlicher Flow, keine speziellen Flex-Eigenschaften */
    }
    
    /* Footer */
    .footer {
      margin-top: 10mm;
      padding-top: 5mm;
      border-top: 1px solid #ccc;
    }
    
    /* Print-spezifisch */
    @media print {
      .page {
        margin: 0;
        padding: 10mm;
      }
      
      * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="header">
      <!-- Header-Inhalt -->
    </div>
    
    <div class="content">
      <!-- Hauptinhalt -->
    </div>
    
    <div class="footer">
      <!-- Footer-Inhalt -->
    </div>
  </div>
</body>
</html>
```

### Zwei-Spalten-Layout

```css
.two-columns {
  display: flex;
  gap: 20px;
}

.column {
  flex: 0 0 48%;  /* Feste Breite */
  /* NICHT: flex: 1 oder flex-grow: 1 */
}
```

### Tabelle für technische Daten

```css
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table td {
  padding: 8px;
  border-bottom: 1px solid #ddd;
}

.data-table td:first-child {
  width: 40%;
  color: #666;
}

.data-table td:last-child {
  font-weight: bold;
}
```

---

## Checkliste vor Änderungen

Bevor du CSS im PDF-Template änderst, prüfe:

- [ ] Verwende ich `min-height` statt `height`?
- [ ] Vermeide ich `flex-grow`, `flex-shrink` auf dem Haupt-Container?
- [ ] Vermeide ich `margin: auto` für Positionierung?
- [ ] Vermeide ich `overflow: hidden` mit festen Höhen?
- [ ] Habe ich `print-color-adjust` für Hintergrundfarben gesetzt?
- [ ] Teste ich die Änderung sofort mit einer PDF-Generierung?
- [ ] Mache ich nur EINE Änderung auf einmal?

---

## Weiterführende Ressourcen

- [WeasyPrint Dokumentation](https://doc.courtbouillon.org/weasyprint/stable/)
- [WeasyPrint CSS Support](https://doc.courtbouillon.org/weasyprint/stable/api_reference.html#css)
- [CSS Paged Media Module](https://www.w3.org/TR/css-page-3/)

---

*Letzte Aktualisierung: November 2025*
*Erstellt nach einem Layout-Bug, der durch übermäßige CSS-Optimierung verursacht wurde.*
