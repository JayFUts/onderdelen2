# OnderdelenLijn.nl Scraper

Een robuuste webscraper voor het verzamelen van auto-onderdelen informatie van onderdelenlijn.nl. De scraper gebruikt Selenium om door de ASP.NET Web Forms pagina's te navigeren en handelt JavaScript-gebaseerde paginatie correct af.

## Kenmerken

- ✅ Automatisch invoeren van kenteken
- ✅ Zoeken naar specifieke onderdelen (bijv. "Accubak")
- ✅ Verwerken van meerdere categorieën
- ✅ Complete paginatie ondersteuning
- ✅ Gedetailleerde product informatie extractie
- ✅ CSV export met alle productgegevens
- ✅ Robuuste foutafhandeling en logging

## Installatie

1. Clone of download dit project
2. Installeer de benodigde dependencies:

```bash
pip install -r requirements.txt
```

## Gebruik

### Basis gebruik

```python
from onderdelenlijn_scraper import OnderdelenLijnScraper

# Maak een scraper instantie
scraper = OnderdelenLijnScraper(headless=True)  # headless=False om browser te zien

# Start het scrapen
scraper.scrape(
    license_plate="27-XH-VX",
    part_name="Accubak",
    output_file="accubak_producten.csv"  # Optioneel, genereert automatisch naam als niet opgegeven
)
```

### Command line gebruik

Het script kan ook direct uitgevoerd worden:

```bash
python onderdelenlijn_scraper.py
```

Dit gebruikt de standaard instellingen uit de `main()` functie.

### Configuratie opties

```python
# Maak scraper met zichtbare browser (voor debugging)
scraper = OnderdelenLijnScraper(headless=False)

# Scrape met custom parameters
scraper.scrape(
    license_plate="AB-12-CD",  # Jouw kenteken
    part_name="Remschijf",     # Het onderdeel dat je zoekt
    output_file="custom_output.csv"
)
```

## Output

De scraper genereert een CSV bestand met de volgende informatie per product:

- **titel**: Product titel/beschrijving
- **prijs**: Prijs van het onderdeel
- **garantie**: Garantieperiode
- **aanbieder**: Naam van de aanbieder
- **afbeelding_url**: URL van de productafbeelding
- **pagina**: Paginanummer waar het product gevonden is
- **categorie_url**: URL van de categorie
- **scraped_at**: Timestamp van het scrapen
- **detail_***: Diverse details zoals Bouwjaar, Tellerstand, Motortype, etc.

## Hoe het werkt

1. **Stap 1 - Kenteken invoeren**: De scraper navigeert naar de startpagina en voert het opgegeven kenteken in
2. **Stap 2 - Categorieën vinden**: Zoekt naar alle categorieën die overeenkomen met het gezochte onderdeel
3. **Stap 3 - Producten scrapen**: Voor elke gevonden categorie:
   - Scrapt alle producten op de huidige pagina
   - Navigeert automatisch door alle pagina's via de "volgende" knop
   - Verzamelt gedetailleerde productinformatie
4. **Stap 4 - Data opslaan**: Slaat alle verzamelde producten op in een CSV bestand

## Logging

De scraper gebruikt Python's logging module voor gedetailleerde status updates:

```
2024-01-15 10:30:45 - INFO - Setting up Chrome driver...
2024-01-15 10:30:48 - INFO - Navigating to start page and entering license plate: 27-XH-VX
2024-01-15 10:30:52 - INFO - Found matching part: Accubak
2024-01-15 10:30:52 - INFO - Categories: 'Motor en Toebehoren', 'Accu en Toebehoren'
2024-01-15 10:30:55 - INFO - Scraping page 1
2024-01-15 10:30:58 - INFO - Found 20 products on page 1
```

## Troubleshooting

### Chrome driver problemen
De scraper gebruikt `webdriver-manager` voor automatisch driver beheer. Als je problemen ondervindt:
- Zorg dat Chrome geïnstalleerd is
- Update naar de laatste versie van Chrome
- Probeer `headless=False` om te zien wat er gebeurt

### Timeout errors
Als je timeout errors krijgt:
- Verhoog de wachttijd in de WebDriverWait instantie
- Controleer je internetverbinding
- De website kan traag zijn tijdens piekuren

### Geen producten gevonden
- Controleer of het kenteken correct is
- Verifieer dat het onderdeel exact overeenkomt met de naam op de website
- Probeer met `headless=False` om te zien wat de scraper doet

## Belangrijke opmerkingen

- Respecteer de website's terms of service
- Gebruik redelijke delays tussen requests
- Deze scraper is voor educatieve doeleinden
- De website structuur kan veranderen, waardoor updates nodig kunnen zijn