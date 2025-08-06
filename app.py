#!/usr/bin/env python3
"""
OnderdelenLijn Dashboard - Web applicatie voor het zoeken van auto-onderdelen
"""

from flask import Flask, render_template, request, jsonify, send_file, make_response
from flask_cors import CORS
import threading
import json
import os
from datetime import datetime
import csv
import io
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from onderdelenlijn_scraper import OnderdelenLijnScraper
from price_analysis import PriceAnalyzer

app = Flask(__name__)
CORS(app)

# Globale variabele voor actieve scraping sessies
active_sessions = {}


class ScrapingSession:
    """Houdt de status bij van een scraping sessie"""
    def __init__(self, session_id):
        self.session_id = session_id
        self.status = "starting"
        self.progress = 0
        self.total_pages = 0
        self.current_page = 0
        self.products = []
        self.error = None
        self.start_time = datetime.now()
        self.selected_categories = []
        

def run_scraper_with_categories(session_id, license_plate, part_name, selected_categories):
    """Voer de scraper uit met geselecteerde categorieën"""
    session = active_sessions[session_id]
    
    try:
        # Update status
        session.status = "running"
        
        # Maak scraper instantie (altijd headless in productie)
        scraper = OnderdelenLijnScraper(headless=True)
        
        try:
            scraper.setup_driver()
            
            # Als er geen categorieën zijn geselecteerd, gebruik de oude methode
            if not selected_categories:
                session.status = "entering_license_plate"
                scraper.enter_license_plate(license_plate)
                
                session.status = "finding_categories"
                category_links = scraper.find_category_links(part_name)
                
                if not category_links:
                    session.error = f"Geen categorieën gevonden voor onderdeel: {part_name}"
                    session.status = "error"
                    return
            else:
                # Gebruik de geselecteerde categorieën
                category_links = [cat['url'] for cat in selected_categories if 'url' in cat]
                print(f"DEBUG: Selected categories count: {len(selected_categories)}")
                print(f"DEBUG: Category links: {category_links}")
                
                if not category_links:
                    session.error = f"Geen geldige URL's gevonden in geselecteerde categorieën"
                    session.status = "error"
                    return
                
            # Stap 3: Scrape elke categorie
            session.status = "scraping"
            for idx, link in enumerate(category_links):
                # Update welke categorie we scrapen
                session.progress = int((idx / len(category_links)) * 100)
                
                # Scrape met aangepaste functie voor progress tracking
                scrape_category_with_progress(scraper, link, session)
                
            session.status = "completed"
            session.progress = 100
            
        finally:
            scraper.close_driver()
            
    except Exception as e:
        session.error = str(e)
        session.status = "error"


def run_scraper(session_id, license_plate, part_name):
    """Achterwaartse compatibiliteit voor de oude scraper functie"""
    return run_scraper_with_categories(session_id, license_plate, part_name, [])
        

def scrape_category_with_progress(scraper, category_url, session):
    """Scrape categorie met progress updates"""
    scraper.driver.get(category_url)
    page_number = 1
    
    while True:
        try:
            # Update huidige pagina
            session.current_page = page_number
            
            # Wacht op producten
            scraper.wait.until(EC.presence_of_element_located((By.ID, "result-list")))
            
            # Kleine delay voor stabiliteit
            import time
            time.sleep(1)
            
            # Vind producten
            product_elements = scraper.driver.find_elements(By.CSS_SELECTOR, "ul#result-list > li")
            
            # Scrape producten
            for product in product_elements:
                try:
                    product_info = scraper.scrape_product_info(product)
                    product_info['pagina'] = page_number
                    session.products.append(product_info)
                except:
                    continue
                    
            # Zoek volgende knop
            try:
                # Verwijder cookie banner
                scraper.driver.execute_script("""
                    var cookieDiv = document.querySelector('div.cookies');
                    if (cookieDiv) cookieDiv.remove();
                    
                    var elements = document.querySelectorAll('[class*="cookie"], [id*="cookie"]');
                    elements.forEach(function(el) {
                        if (el.style.position === 'fixed' || el.style.position === 'absolute') {
                            el.remove();
                        }
                    });
                """)
                
                next_button = scraper.driver.find_element(
                    By.CSS_SELECTOR, 'span.pagination input[value=">"]:not([disabled])'
                )
                
                # Klik volgende
                scraper.driver.execute_script("arguments[0].click();", next_button)
                page_number += 1
                
                # Wacht op refresh
                time.sleep(1.5)
                
            except:
                # Geen volgende pagina meer
                break
                
        except Exception as e:
            break
            

@app.route('/')
def index():
    """Hoofdpagina met het dashboard"""
    return render_template('dashboard.html')


@app.route('/api/categories', methods=['POST'])
def get_categories():
    """Haal alle beschikbare categorieën op voor een onderdeel"""
    data = request.json
    license_plate = data.get('license_plate', '').upper().replace('-', '')
    part_name = data.get('part_name', '')
    
    # Validatie
    if not license_plate or not part_name:
        return jsonify({'error': 'Kenteken en onderdeel zijn verplicht'}), 400
        
    # Format kenteken
    if len(license_plate) == 6:
        formatted_plate = f"{license_plate[:2]}-{license_plate[2:4]}-{license_plate[4:]}"
    else:
        formatted_plate = license_plate
        
    try:
        # Maak tijdelijke scraper om categorieën op te halen
        scraper = OnderdelenLijnScraper(headless=True)
        scraper.setup_driver()
        
        try:
            # Voer kenteken in
            scraper.enter_license_plate(formatted_plate)
            
            # Vind alle categorieën die matchen met het onderdeel
            all_categories = find_all_matching_categories(scraper, part_name)
            
            return jsonify({
                'categories': all_categories,
                'total': len(all_categories)
            })
            
        finally:
            scraper.close_driver()
            
    except Exception as e:
        return jsonify({'error': f'Er is een fout opgetreden: {str(e)}'}), 500


def find_all_matching_categories(scraper, part_name):
    """Vind alle categorieën die matchen met het gezochte onderdeel"""
    categories = []
    
    try:
        # Wacht tot de search results list aanwezig is
        scraper.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-results-list")))
        
        # Vind alle onderdeel links
        part_elements = scraper.driver.find_elements(By.CSS_SELECTOR, "div.search-results-list a")
        
        # Zoek naar alle mogelijke matches
        search_terms = [part_name.lower()]
        
        # Voeg extra zoektermen toe voor veelvoorkomende onderdelen
        if 'rem' in part_name.lower():
            search_terms.extend(['remschijf', 'remblok', 'remklauw', 'handrem'])
        if 'accu' in part_name.lower():
            search_terms.extend(['accubak', 'batterij'])
        if 'motor' in part_name.lower():
            search_terms.extend(['motorblok', 'motor', 'aandrijving'])
        if 'uitlaat' in part_name.lower():
            search_terms.extend(['uitlaatsysteem', 'demper', 'katalysator'])
        if 'bumper' in part_name.lower():
            search_terms.extend(['voorbumper', 'achterbumper'])
        if 'koplamp' in part_name.lower():
            search_terms.extend(['koplamp', 'achterlicht', 'verlichting'])
            
        found_urls = set()  # Voorkom duplicaten
        
        for element in part_elements:
            element_text = element.text.strip().lower()
            element_title = (element.get_attribute('title') or '').strip().lower()
            
            # Check of een van de zoektermen matcht
            for search_term in search_terms:
                if search_term in element_text or search_term in element_title:
                    href = element.get_attribute('href')
                    if href and href not in found_urls:
                        found_urls.add(href)
                        
                        # Haal extra info op
                        data_category = element.get_attribute('data-category') or ''
                        
                        # Maak volledige URL indien nodig
                        if not href.startswith('http'):
                            full_url = scraper.base_url + href
                        else:
                            full_url = href
                            
                        categories.append({
                            'name': element.get_attribute('title') or element.text.strip(),
                            'url': full_url,
                            'description': f"Categorieën: {data_category}" if data_category else '',
                            'search_term': search_term
                        })
                    break
                    
        return categories
        
    except Exception as e:
        print(f"Error finding categories: {e}")
        return []


@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    """Start een nieuwe scraping sessie met geselecteerde categorieën"""
    data = request.json
    license_plate = data.get('license_plate', '').upper().replace('-', '')
    part_name = data.get('part_name', '')
    selected_categories = data.get('selected_categories', [])
    
    # Validatie
    if not license_plate or not part_name:
        return jsonify({'error': 'Kenteken en onderdeel zijn verplicht'}), 400
        
    # Format kenteken (voeg streepjes toe)
    if len(license_plate) == 6:
        formatted_plate = f"{license_plate[:2]}-{license_plate[2:4]}-{license_plate[4:]}"
    else:
        formatted_plate = license_plate
        
    # Maak sessie ID
    session_id = f"{license_plate}_{part_name}_{datetime.now().timestamp()}"
    
    # Maak nieuwe sessie
    session = ScrapingSession(session_id)
    session.selected_categories = selected_categories
    active_sessions[session_id] = session
    
    # Start scraper in achtergrond
    thread = threading.Thread(
        target=run_scraper_with_categories,
        args=(session_id, formatted_plate, part_name, selected_categories)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'session_id': session_id,
        'status': 'started'
    })


@app.route('/api/status/<session_id>')
def get_status(session_id):
    """Haal de status op van een scraping sessie"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Sessie niet gevonden'}), 404
        
    session = active_sessions[session_id]
    
    return jsonify({
        'status': session.status,
        'progress': session.progress,
        'current_page': session.current_page,
        'product_count': len(session.products),
        'error': session.error
    })


@app.route('/api/results/<session_id>')
def get_results(session_id):
    """Haal de resultaten op van een voltooide scraping sessie"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Sessie niet gevonden'}), 404
        
    session = active_sessions[session_id]
    
    # Format producten voor display met platte structuur
    formatted_products = []
    for product in session.products:
        formatted_product = {
            'product_id': product.get('product_id', 'Onbekend'),
            'titel': product.get('titel', 'Onbekend'),
            'soort_onderdeel': product.get('soort_onderdeel', 'Onbekend'),
            'prijs': product.get('prijs', 'Onbekend'),
            'prijs_numeriek': product.get('prijs_numeriek', 0.0),
            'prijs_type': product.get('prijs_type', 'Standaard'),
            'garantie': product.get('garantie', 'Onbekend'),
            'aanbieder': product.get('aanbieder', 'Onbekend'),
            'afbeelding_url': product.get('afbeelding_url', ''),
            'product_url': product.get('product_url', ''),
            'opmerkingen': product.get('opmerkingen', 'Geen opmerkingen'),
            'match_beschrijving': product.get('match_beschrijving', 'Geen match info'),
            'match_kleur': product.get('match_kleur', 'unknown'),
            'direct_bestelbaar': product.get('direct_bestelbaar', False),
            'pagina': product.get('pagina', 1),
            'scraped_at': product.get('scraped_at', ''),
            'scrape_timestamp': product.get('scrape_timestamp', 0)
        }
        
        # Voeg specificaties toe als platte spec_ velden
        if 'specificaties' in product and product['specificaties']:
            for key, value in product['specificaties'].items():
                # Normaliseer de key voor CSV compatibiliteit
                normalized_key = key.replace(' ', '_').replace('/', '_').replace('-', '_').lower()
                formatted_product[f'spec_{normalized_key}'] = value
                
        # Backwards compatibility: ook oude 'details' velden ondersteunen
        if 'details' in product and product['details']:
            for key, value in product['details'].items():
                normalized_key = key.replace(' ', '_').replace('/', '_').replace('-', '_').lower()
                formatted_product[f'detail_{normalized_key}'] = value
                
        formatted_products.append(formatted_product)
    
    return jsonify({
        'products': formatted_products,
        'total': len(formatted_products),
        'duration': str(datetime.now() - session.start_time)
    })


@app.route('/api/export/<session_id>')
def export_results(session_id):
    """Exporteer resultaten als CSV"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Sessie niet gevonden'}), 404
        
    session = active_sessions[session_id]
    
    # Maak CSV in memory
    output = io.StringIO()
    
    if session.products:
        # Bepaal alle velden inclusief platte specificaties
        all_keys = set()
        for product in session.products:
            # Voeg basis velden toe
            all_keys.update(product.keys())
            
            # Voeg specificaties toe als platte spec_ velden
            if 'specificaties' in product and product['specificaties']:
                for key in product['specificaties'].keys():
                    normalized_key = key.replace(' ', '_').replace('/', '_').replace('-', '_').lower()
                    all_keys.add(f"spec_{normalized_key}")
                    
            # Backwards compatibility: ook oude 'details' velden
            if 'details' in product and product['details']:
                for key in product['details'].keys():
                    normalized_key = key.replace(' ', '_').replace('/', '_').replace('-', '_').lower()
                    all_keys.add(f"detail_{normalized_key}")
                
        # Verwijder geneste dictionaries uit de keys
        all_keys.discard('specificaties')
        all_keys.discard('details')
        fieldnames = sorted(all_keys)
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for product in session.products:
            row = product.copy()
            
            # Converteer specificaties naar platte structuur
            if 'specificaties' in row:
                specificaties = row.pop('specificaties')
                for key, value in specificaties.items():
                    normalized_key = key.replace(' ', '_').replace('/', '_').replace('-', '_').lower()
                    row[f"spec_{normalized_key}"] = value
            
            # Backwards compatibility: ook oude 'details' velden
            if 'details' in row:
                details = row.pop('details')
                for key, value in details.items():
                    normalized_key = key.replace(' ', '_').replace('/', '_').replace('-', '_').lower()
                    row[f"detail_{normalized_key}"] = value
                    
            writer.writerow(row)
    
    # Zet pointer terug naar begin
    output.seek(0)
    
    # Maak response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=onderdelenlijn_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response


@app.route('/api/price-analysis/<session_id>')
def get_price_analysis(session_id):
    """Krijg prijsanalyse van een voltooide scraping sessie"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Sessie niet gevonden'}), 404
        
    session = active_sessions[session_id]
    
    if not session.products:
        return jsonify({'error': 'Geen producten beschikbaar voor analyse'}), 400
    
    # Check voor categorie filter
    category = request.args.get('category')
    
    try:
        # Maak prijsanalyse
        analyzer = PriceAnalyzer(session.products)
        report = analyzer.generate_market_report(category)
        report['gegenereerd_op'] = datetime.now().isoformat()
        
        return jsonify(report)
        
    except Exception as e:
        return jsonify({'error': f'Fout bij prijsanalyse: {str(e)}'}), 500


@app.route('/api/price-recommendations/<session_id>')
def get_price_recommendations(session_id):
    """Krijg specifieke prijsaanbevelingen"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Sessie niet gevonden'}), 404
        
    session = active_sessions[session_id]
    
    if not session.products:
        return jsonify({'error': 'Geen producten beschikbaar'}), 400
    
    # Check voor categorie filter
    category = request.args.get('category')
    
    try:
        analyzer = PriceAnalyzer(session.products)
        
        if category:
            analyzer = analyzer.filter_by_category(category)
            
        recommendations = analyzer.get_price_recommendations()
        
        return jsonify({
            'categorie': category,
            'aanbevelingen': recommendations,
            'markt_statistieken': analyzer.get_overall_statistics(),
            'gegenereerd_op': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Fout bij prijsaanbevelingen: {str(e)}'}), 500


@app.route('/api/competitive-analysis/<session_id>')
def get_competitive_analysis(session_id):
    """Krijg concurrentieanalyse met target prijs"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Sessie niet gevonden'}), 404
        
    target_price = request.args.get('target_price', type=float)
    margin = request.args.get('margin', default=0.1, type=float)
    category = request.args.get('category')
    
    session = active_sessions[session_id]
    
    if not session.products:
        return jsonify({'error': 'Geen producten beschikbaar'}), 400
    
    try:
        analyzer = PriceAnalyzer(session.products)
        
        if category:
            analyzer = analyzer.filter_by_category(category)
            
        competitive_products = analyzer.get_competitive_products(target_price, margin)
        
        return jsonify({
            'categorie': category,
            'target_prijs': target_price,
            'marge_percentage': margin * 100,
            'concurrerende_producten': competitive_products,
            'aantal_gevonden': len(competitive_products),
            'gegenereerd_op': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Fout bij concurrentieanalyse: {str(e)}'}), 500


if __name__ == '__main__':
    # Maak templates directory als die niet bestaat
    os.makedirs('templates', exist_ok=True)
    
    # Get port from environment (Railway sets PORT automatically)
    port = int(os.environ.get('PORT', 5000))
    
    # Start de Flask app
    app.run(debug=False, host='0.0.0.0', port=port)