#!/usr/bin/env python3
"""
Voorbeeld gebruik van de OnderdelenLijn scraper
"""

from onderdelenlijn_scraper import OnderdelenLijnScraper

def main():
    # Configuratie
    LICENSE_PLATE = "27-XH-VX"
    PART_NAME = "Accubak"
    
    # Maak scraper instantie
    # headless=True voor achtergrond uitvoering
    # headless=False om browser te zien (handig voor debugging)
    scraper = OnderdelenLijnScraper(headless=True)
    
    # Start het scrapen
    # De scraper zal automatisch:
    # 1. Het kenteken invoeren
    # 2. Naar het juiste onderdeel zoeken
    # 3. Alle pagina's doorlopen
    # 4. Resultaten opslaan in CSV
    scraper.scrape(
        license_plate=LICENSE_PLATE,
        part_name=PART_NAME,
        output_file=f"accubak_producten_{LICENSE_PLATE}.csv"
    )
    
    print(f"\nScraping voltooid! Totaal {len(scraper.products)} producten gevonden.")
    
    # Toon enkele voorbeelden
    if scraper.products:
        print("\nEerste 3 producten:")
        for i, product in enumerate(scraper.products[:3], 1):
            print(f"\n{i}. {product['titel']}")
            print(f"   Prijs: {product['prijs']}")
            print(f"   Garantie: {product['garantie']}")
            if 'details' in product and product['details']:
                print(f"   Details: {', '.join(f'{k}: {v}' for k, v in product['details'].items())}")


if __name__ == "__main__":
    main()