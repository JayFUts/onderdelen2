#!/usr/bin/env python3
"""
OnderdelenLijn.nl Scraper
========================
Een robuuste scraper voor het verzamelen van auto-onderdelen van onderdelenlijn.nl
Gebruikt Selenium voor het navigeren door ASP.NET Web Forms pagina's met JavaScript-based paginatie.
"""

import time
import csv
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configureer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OnderdelenLijnScraper:
    """Scraper voor het verzamelen van auto-onderdelen van onderdelenlijn.nl"""
    
    def __init__(self, headless=True):
        """
        Initialiseer de scraper
        
        Args:
            headless (bool): Run browser in headless mode (zonder UI)
        """
        self.base_url = "https://www.onderdelenlijn.nl"
        self.start_url = f"{self.base_url}/auto-onderdelen-voorraad/zoeken/"
        self.driver = None
        self.wait = None
        self.headless = headless
        self.products = []
        
    def setup_driver(self):
        """Configureer en start de Chrome webdriver"""
        logger.info("Setting up Chrome driver...")
        
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        # Essential Chrome arguments for server environment
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent to avoid detection
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Gebruik webdriver_manager voor automatisch driver beheer
        driver_path = ChromeDriverManager().install()
        # Fix voor webdriver-manager pad probleem
        if driver_path.endswith('THIRD_PARTY_NOTICES.chromedriver'):
            driver_path = driver_path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
        
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 20)
        
        logger.info("Chrome driver setup complete")
        
    def close_driver(self):
        """Sluit de webdriver"""
        if self.driver:
            self.driver.quit()
            logger.info("Chrome driver closed")
            
    def enter_license_plate(self, license_plate):
        """
        Voer het kenteken in op de startpagina (Stap 1)
        
        Args:
            license_plate (str): Het kenteken om te zoeken
        """
        logger.info(f"Navigating to start page and entering license plate: {license_plate}")
        
        try:
            # Ga naar de startpagina
            self.driver.get(self.start_url)
            
            # Probeer cookie banner te verwijderen
            try:
                # Wacht kort op pagina laden
                time.sleep(2)
                
                # Verwijder cookie div met JavaScript
                self.driver.execute_script("""
                    var cookieDiv = document.querySelector('div.cookies');
                    if (cookieDiv) {
                        cookieDiv.remove();
                        console.log('Cookie div removed');
                    }
                    
                    // Probeer ook andere mogelijke cookie elementen te verwijderen
                    var elements = document.querySelectorAll('[class*="cookie"], [id*="cookie"], [class*="consent"], [id*="consent"]');
                    elements.forEach(function(el) {
                        if (el.style.position === 'fixed' || el.style.position === 'absolute') {
                            el.remove();
                        }
                    });
                """)
                logger.info("Cookie banner removed via JavaScript")
                time.sleep(0.5)
            except Exception as e:
                logger.info(f"Could not remove cookie banner: {e}")
            
            # Wacht tot het kenteken invoerveld aanwezig is
            license_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "objlicenseplate"))
            )
            
            # Vul het kenteken in
            license_input.clear()
            license_input.send_keys(license_plate)
            
            # Klik op de "Gegevens ophalen" knop
            submit_button = self.driver.find_element(By.NAME, "m$mpc$ctl17")
            
            # Probeer verschillende methoden om te klikken
            try:
                submit_button.click()
            except:
                try:
                    # Probeer JavaScript click
                    self.driver.execute_script("arguments[0].click();", submit_button)
                    logger.info("Used JavaScript click for submit button")
                except:
                    # Probeer Actions chain
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_to_element(submit_button).click().perform()
                    logger.info("Used ActionChains click for submit button")
            
            # Wacht tot de volgende pagina is geladen (check voor parts div)
            self.wait.until(
                EC.presence_of_element_located((By.ID, "parts"))
            )
            
            logger.info("Successfully entered license plate and navigated to parts page")
            
        except TimeoutException:
            logger.error("Timeout waiting for page elements")
            raise
        except Exception as e:
            logger.error(f"Error entering license plate: {e}")
            raise
            
    def find_category_links(self, part_name):
        """
        Vind alle categorie links voor het gezochte onderdeel (Stap 2)
        
        Args:
            part_name (str): Naam van het onderdeel (bijv. "Accubak")
            
        Returns:
            list: Lijst van URLs voor de gevonden categorieën
        """
        logger.info(f"Searching for category links for part: {part_name}")
        
        category_links = []
        
        try:
            # Wacht tot de search results list aanwezig is
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-results-list"))
            )
            
            # Vind alle onderdeel links
            part_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "div.search-results-list a"
            )
            
            for element in part_elements:
                # Check zowel de tekst als het title attribuut
                element_text = element.text.strip()
                element_title = element.get_attribute('title').strip()
                
                if part_name.lower() in element_text.lower() or part_name.lower() in element_title.lower():
                    href = element.get_attribute('href')
                    categories = element.get_attribute('data-category')
                    
                    logger.info(f"Found matching part: {element_title}")
                    logger.info(f"Categories: {categories}")
                    logger.info(f"URL: {href}")
                    
                    category_links.append(href)
                    
            logger.info(f"Found {len(category_links)} category link(s)")
            
        except Exception as e:
            logger.error(f"Error finding category links: {e}")
            raise
            
        return category_links
        
    def scrape_product_info(self, product_element):
        """
        Dynamische productinformatie extractie met correcte selectors
        Gebaseerd op de werkelijke HTML structuur van onderdelenlijn.nl
        """
        product_data = {}
        
        try:
            logger.info("=== STARTING PRODUCT SCRAPE ===")
            
            # === BASISGEGEVENS MET JUISTE SELECTORS ===
            
            # Product ID - uit data-gtm-id attribuut
            try:
                product_id = product_element.get_attribute('data-gtm-id')
                if product_id:
                    product_data['product_id'] = product_id.replace('P', '') if product_id.startswith('P') else product_id
                    logger.info(f"Product ID: {product_data['product_id']}")
                else:
                    product_data['product_id'] = "Onbekend"
            except Exception as e:
                logger.error(f"Error extracting product ID: {e}")
                product_data['product_id'] = "Onbekend"
            
            # Product URL - uit onclick attribuut
            try:
                onclick_attr = product_element.get_attribute('onclick')
                if onclick_attr and 'window.location.href' in onclick_attr:
                    import re
                    url_match = re.search(r"window\.location\.href='([^']+)'", onclick_attr)
                    if url_match:
                        relative_url = url_match.group(1)
                        product_data['product_url'] = self.base_url + relative_url if not relative_url.startswith('http') else relative_url
                        logger.info(f"Product URL: {product_data['product_url']}")
                    else:
                        product_data['product_url'] = "Geen URL"
                else:
                    product_data['product_url'] = "Geen URL"
            except Exception as e:
                logger.error(f"Error extracting product URL: {e}")
                product_data['product_url'] = "Geen URL"
            
            # Titel - uit span.bold
            try:
                title_elem = product_element.find_element(By.CSS_SELECTOR, "span.bold")
                product_data['titel'] = title_elem.text.strip()
                logger.info(f"Titel: {product_data['titel']}")
            except Exception as e:
                logger.error(f"Error extracting title: {e}")
                product_data['titel'] = "Geen titel"
            
            # Soort Onderdeel - uit eerste <p> in div.description
            try:
                soort_elem = product_element.find_element(By.CSS_SELECTOR, "div.description p")
                product_data['soort_onderdeel'] = soort_elem.text.strip()
                logger.info(f"Soort onderdeel: {product_data['soort_onderdeel']}")
            except Exception as e:
                logger.error(f"Error extracting soort onderdeel: {e}")
                product_data['soort_onderdeel'] = "Onbekend"
            
            # Prijs - uit span.price
            try:
                price_elem = product_element.find_element(By.CSS_SELECTOR, "span.price")
                product_data['prijs'] = price_elem.text.strip()
                
                # Extract numerical value
                import re
                price_match = re.search(r'€\s*([0-9.,]+)', product_data['prijs'])
                if price_match:
                    product_data['prijs_numeriek'] = float(price_match.group(1).replace(',', '.'))
                else:
                    product_data['prijs_numeriek'] = 0.0
                    
                logger.info(f"Prijs: {product_data['prijs']}")
                
            except Exception as e:
                logger.error(f"Error extracting price: {e}")
                product_data['prijs'] = "Prijs op aanvraag"
                product_data['prijs_numeriek'] = 0.0
            
            # Prijs Type - uit span binnen span.price (alleen als er een geneste span is)
            try:
                price_type_elem = product_element.find_element(By.CSS_SELECTOR, "span.price span")
                product_data['prijs_type'] = price_type_elem.text.strip()
                logger.info(f"Prijs type: {product_data['prijs_type']}")
            except Exception as e:
                # Voor "Prijs op aanvraag" producten is er geen geneste span
                if "Prijs op aanvraag" in product_data.get('prijs', ''):
                    product_data['prijs_type'] = "Op aanvraag"
                    logger.info(f"Prijs type: {product_data['prijs_type']} (detected from price text)")
                else:
                    product_data['prijs_type'] = "Standaard"
                    logger.debug(f"Could not extract price type, using default: {e}")
            
            # Garantie - uit div.pricing p
            try:
                garantie_elem = product_element.find_element(By.CSS_SELECTOR, "div.pricing p")
                garantie_text = garantie_elem.text.strip()
                if 'Garantie' in garantie_text:
                    product_data['garantie'] = garantie_text.replace('Garantie:', '').replace('Garantie', '').strip()
                else:
                    product_data['garantie'] = garantie_text
                logger.info(f"Garantie: {product_data['garantie']}")
            except Exception as e:
                logger.error(f"Error extracting garantie: {e}")
                product_data['garantie'] = "Onbekend"
            
            # Aanbieder - uit div.pricing .block
            try:
                aanbieder_elem = product_element.find_element(By.CSS_SELECTOR, "div.pricing .block")
                product_data['aanbieder'] = aanbieder_elem.text.strip()
                logger.info(f"Aanbieder: {product_data['aanbieder']}")
            except Exception as e:
                logger.error(f"Error extracting aanbieder: {e}")
                product_data['aanbieder'] = "Onbekend"
            
            # Afbeelding URL - uit img.img-responsive
            try:
                img_elem = product_element.find_element(By.CSS_SELECTOR, "img.img-responsive")
                product_data['afbeelding_url'] = img_elem.get_attribute('src')
                logger.info(f"Afbeelding URL: {product_data['afbeelding_url']}")
            except Exception as e:
                logger.error(f"Error extracting image: {e}")
                product_data['afbeelding_url'] = "Geen afbeelding"
            
            # === DYNAMISCHE SPECIFICATIES (KERNFUNCTIE) ===
            logger.info("=== EXTRACTING SPECIFICATIONS ===")
            specificaties = {}
            
            try:
                # Zoek naar alle specificatie containers: div.description p span.item
                spec_containers = product_element.find_elements(By.CSS_SELECTOR, "div.description p span.item")
                logger.info(f"Found {len(spec_containers)} specification containers")
                
                for i, container in enumerate(spec_containers):
                    try:
                        # Vind sleutel: span.grey
                        key_elem = container.find_element(By.CSS_SELECTOR, "span.grey")
                        key = key_elem.text.strip()
                        
                        # Vind waarde: span.grey + span (Adjacent Sibling Selector)
                        try:
                            value_elem = container.find_element(By.CSS_SELECTOR, "span.grey + span")
                            value = value_elem.text.strip()
                        except:
                            # Fallback: extract from full text
                            full_text = container.text.strip()
                            value = full_text.replace(key, '').strip()
                        
                        if key and value:
                            specificaties[key] = value
                            logger.info(f"  Spec {i+1}: {key} = {value}")
                        
                    except Exception as e:
                        logger.error(f"Error processing specification container {i}: {e}")
                        continue
                
                product_data['specificaties'] = specificaties
                logger.info(f"Total specifications extracted: {len(specificaties)}")
                
            except Exception as e:
                logger.error(f"Error extracting specifications: {e}")
                product_data['specificaties'] = {}
            
            # === OVERIGE METADATA ===
            
            # Opmerkingen - tekst na <span class="grey">Bijzonderheid</span>
            try:
                # Zoek naar Bijzonderheid span en haal de tekst eromheen op
                bijzonderheid_elems = product_element.find_elements(By.XPATH, ".//span[@class='grey'][contains(text(), 'Bijzonderheid')]")
                if bijzonderheid_elems:
                    # Haal de parent paragraph op en extract de tekst
                    parent_p = bijzonderheid_elems[0].find_element(By.XPATH, "./..")
                    full_text = parent_p.text.strip()
                    product_data['opmerkingen'] = full_text.replace('Bijzonderheid', '').strip()
                else:
                    product_data['opmerkingen'] = "Geen opmerkingen"
                logger.info(f"Opmerkingen: {product_data['opmerkingen']}")
            except Exception as e:
                logger.error(f"Error extracting opmerkingen: {e}")
                product_data['opmerkingen'] = "Geen opmerkingen"
            
            # Match Kans - title attribuut van <p> met match-indicator
            try:
                match_elem = product_element.find_element(By.CSS_SELECTOR, "p[title*='match'], p[title*='Match']")
                product_data['match_beschrijving'] = match_elem.get_attribute('title')
                logger.info(f"Match beschrijving: {product_data['match_beschrijving']}")
            except Exception as e:
                logger.error(f"Error extracting match beschrijving: {e}")
                product_data['match_beschrijving'] = "Geen match info"
            
            # Match Kleur - class uit span.match
            try:
                match_span = product_element.find_element(By.CSS_SELECTOR, "span.match")
                match_classes = match_span.get_attribute('class')
                if 'green' in match_classes:
                    product_data['match_kleur'] = 'green'
                elif 'orange' in match_classes:
                    product_data['match_kleur'] = 'orange'
                elif 'red' in match_classes:
                    product_data['match_kleur'] = 'red'
                else:
                    product_data['match_kleur'] = 'unknown'
                logger.info(f"Match kleur: {product_data['match_kleur']}")
            except Exception as e:
                logger.error(f"Error extracting match kleur: {e}")
                product_data['match_kleur'] = 'unknown'
            
            # Direct Bestelbaar - boolean op basis van p.order-directly
            try:
                order_elem = product_element.find_element(By.CSS_SELECTOR, "p.order-directly")
                product_data['direct_bestelbaar'] = True
                logger.info("Direct bestelbaar: True")
            except:
                product_data['direct_bestelbaar'] = False
                logger.info("Direct bestelbaar: False")
            
            # === METADATA ===
            product_data['scraped_at'] = datetime.now().isoformat()
            product_data['scrape_timestamp'] = int(datetime.now().timestamp())
            
            logger.info("=== PRODUCT SCRAPE COMPLETE ===")
            
        except Exception as e:
            logger.error(f"Critical error in scrape_product_info: {e}")
            
        return product_data
        
    def scrape_category_with_pagination(self, category_url):
        """
        Scrape alle producten uit een categorie inclusief alle pagina's (Stap 3)
        
        Args:
            category_url (str): URL van de categorie om te scrapen
        """
        logger.info(f"Scraping category: {category_url}")
        
        # Navigeer naar de categorie
        self.driver.get(category_url)
        
        page_number = 1
        
        while True:
            logger.info(f"Scraping page {page_number}")
            
            try:
                # Wacht tot de product lijst geladen is
                self.wait.until(
                    EC.presence_of_element_located((By.ID, "result-list"))
                )
                
                # Kleine delay om de pagina volledig te laten laden
                time.sleep(1)
                
                # Vind alle producten op de huidige pagina
                product_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, "ul#result-list > li"
                )
                
                logger.info(f"Found {len(product_elements)} products on page {page_number}")
                
                # Scrape elk product
                for idx, product in enumerate(product_elements):
                    try:
                        product_info = self.scrape_product_info(product)
                        product_info['pagina'] = page_number
                        product_info['categorie_url'] = category_url
                        self.products.append(product_info)
                    except StaleElementReferenceException:
                        logger.warning(f"Stale element on product {idx}, skipping...")
                        continue
                        
                # Zoek de "volgende" knop
                try:
                    # Zoek alleen actieve (niet-disabled) volgende knoppen
                    next_button = self.driver.find_element(
                        By.CSS_SELECTOR, 'span.pagination input[value=">"]:not([disabled])'
                    )
                    
                    # Scroll naar de knop voor zekerheid
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(0.5)
                    
                    # Verwijder eerst eventuele cookie banners
                    self.driver.execute_script("""
                        var cookieDiv = document.querySelector('div.cookies');
                        if (cookieDiv) cookieDiv.remove();
                        
                        var elements = document.querySelectorAll('[class*="cookie"], [id*="cookie"], [class*="consent"], [id*="consent"]');
                        elements.forEach(function(el) {
                            if (el.style.position === 'fixed' || el.style.position === 'absolute') {
                                el.remove();
                            }
                        });
                    """)
                    
                    # Klik op de volgende knop
                    try:
                        next_button.click()
                    except:
                        # Gebruik JavaScript als normale click niet werkt
                        self.driver.execute_script("arguments[0].click();", next_button)
                    
                    # Wacht tot de content is vernieuwd
                    # We wachten tot het eerste product element "stale" wordt
                    old_first_product = product_elements[0] if product_elements else None
                    if old_first_product:
                        self.wait.until(EC.staleness_of(old_first_product))
                    
                    page_number += 1
                    
                except NoSuchElementException:
                    logger.info("No more pages available")
                    break
                    
            except TimeoutException:
                logger.error(f"Timeout on page {page_number}")
                break
            except Exception as e:
                logger.error(f"Error on page {page_number}: {e}")
                break
                
        logger.info(f"Finished scraping category. Total products: {len(self.products)}")
        
    def save_to_csv(self, filename):
        """
        Sla de verzamelde producten op in een CSV bestand met platte structuur
        
        Args:
            filename (str): Naam van het output bestand
        """
        if not self.products:
            logger.warning("No products to save")
            return
            
        logger.info(f"Saving {len(self.products)} products to {filename}")
        
        # Bepaal alle mogelijke velden inclusief platte specificaties
        all_keys = set()
        for product in self.products:
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
        
        # Sorteer de velden voor consistentie
        fieldnames = sorted(all_keys)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in self.products:
                # Kopieer product data
                row = product.copy()
                
                # Converteer specificaties naar platte structuur
                if 'specificaties' in row:
                    specificaties = row.pop('specificaties')
                    for key, value in specificaties.items():
                        normalized_key = key.replace(' ', '_').replace('/', '_').replace('-', '_').lower()
                        row[f"spec_{normalized_key}"] = value
                
                # Backwards compatibility: pak oude details uit
                if 'details' in row:
                    details = row.pop('details')
                    for key, value in details.items():
                        normalized_key = key.replace(' ', '_').replace('/', '_').replace('-', '_').lower()
                        row[f"detail_{normalized_key}"] = value
                        
                writer.writerow(row)
                
        logger.info(f"Successfully saved products to {filename}")
        
    def scrape(self, license_plate, part_name, output_file=None):
        """
        Hoofdfunctie om het complete scraping proces uit te voeren
        
        Args:
            license_plate (str): Kenteken om te zoeken
            part_name (str): Naam van het onderdeel
            output_file (str): Output CSV bestandsnaam (optioneel)
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"onderdelenlijn_{license_plate}_{part_name}_{timestamp}.csv"
            
        try:
            # Setup driver
            self.setup_driver()
            
            # Stap 1: Voer kenteken in
            self.enter_license_plate(license_plate)
            
            # Stap 2: Vind categorie links
            category_links = self.find_category_links(part_name)
            
            if not category_links:
                logger.warning(f"No categories found for part: {part_name}")
                return
                
            # Stap 3: Scrape elke categorie
            for idx, link in enumerate(category_links):
                logger.info(f"Processing category {idx + 1} of {len(category_links)}")
                self.scrape_category_with_pagination(link)
                
            # Stap 4: Sla resultaten op
            self.save_to_csv(output_file)
            
            logger.info(f"Scraping completed successfully. Total products: {len(self.products)}")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise
        finally:
            self.close_driver()


def main():
    """Voorbeeld gebruik van de scraper"""
    # Configuratie
    LICENSE_PLATE = "27-XH-VX"
    PART_NAME = "Accubak"
    
    # Maak scraper instantie  
    scraper = OnderdelenLijnScraper(headless=False)  # headless=False om browser te zien
    
    # Start het scrapen
    scraper.scrape(LICENSE_PLATE, PART_NAME)


if __name__ == "__main__":
    main()