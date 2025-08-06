#!/usr/bin/env python3
"""
OnderdelenLijn.nl Scraper - Playwright Versie
============================================
Een alternatieve versie van de scraper die Playwright gebruikt in plaats van Selenium.
Playwright biedt betere performance en modernere browser automatisering.
"""

import asyncio
import csv
import logging
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Configureer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OnderdelenLijnScraperPlaywright:
    """Playwright-gebaseerde scraper voor onderdelenlijn.nl"""
    
    def __init__(self, headless=True):
        """
        Initialiseer de scraper
        
        Args:
            headless (bool): Run browser in headless mode
        """
        self.base_url = "https://www.onderdelenlijn.nl"
        self.start_url = f"{self.base_url}/auto-onderdelen-voorraad/zoeken/"
        self.headless = headless
        self.products = []
        self.page = None
        self.browser = None
        self.playwright = None
        
    async def setup_browser(self):
        """Setup Playwright browser"""
        logger.info("Setting up Playwright browser...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Maak een nieuwe browser context met custom user agent
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await context.new_page()
        logger.info("Playwright browser setup complete")
        
    async def close_browser(self):
        """Sluit de browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")
        
    async def enter_license_plate(self, license_plate):
        """
        Voer het kenteken in op de startpagina (Stap 1)
        
        Args:
            license_plate (str): Het kenteken om te zoeken
        """
        logger.info(f"Navigating to start page and entering license plate: {license_plate}")
        
        try:
            # Ga naar de startpagina
            await self.page.goto(self.start_url, wait_until='networkidle')
            
            # Vul het kenteken in
            await self.page.fill('#objlicenseplate', license_plate)
            
            # Klik op de "Gegevens ophalen" knop
            await self.page.click('[name="m$mpc$ctl17"]')
            
            # Wacht tot de volgende pagina is geladen
            await self.page.wait_for_selector('#parts', timeout=20000)
            
            logger.info("Successfully entered license plate and navigated to parts page")
            
        except PlaywrightTimeout:
            logger.error("Timeout waiting for page elements")
            raise
        except Exception as e:
            logger.error(f"Error entering license plate: {e}")
            raise
            
    async def find_category_links(self, part_name):
        """
        Vind alle categorie links voor het gezochte onderdeel (Stap 2)
        
        Args:
            part_name (str): Naam van het onderdeel
            
        Returns:
            list: Lijst van URLs voor de gevonden categorieën
        """
        logger.info(f"Searching for category links for part: {part_name}")
        
        category_links = []
        
        try:
            # Wacht tot de search results aanwezig zijn
            await self.page.wait_for_selector('.search-results-list', timeout=10000)
            
            # Vind alle onderdeel links
            part_elements = await self.page.query_selector_all('div.search-results-list a')
            
            for element in part_elements:
                # Haal tekst en attributen op
                element_text = await element.inner_text()
                element_title = await element.get_attribute('title') or ''
                
                if part_name.lower() in element_text.lower() or part_name.lower() in element_title.lower():
                    href = await element.get_attribute('href')
                    categories = await element.get_attribute('data-category')
                    
                    # Maak volledige URL
                    if href and not href.startswith('http'):
                        href = self.base_url + href
                        
                    logger.info(f"Found matching part: {element_title or element_text}")
                    logger.info(f"Categories: {categories}")
                    logger.info(f"URL: {href}")
                    
                    category_links.append(href)
                    
            logger.info(f"Found {len(category_links)} category link(s)")
            
        except Exception as e:
            logger.error(f"Error finding category links: {e}")
            raise
            
        return category_links
        
    async def scrape_product_info(self, product_element):
        """
        Haal productinformatie uit een enkel product element
        
        Args:
            product_element: Playwright element voor een product
            
        Returns:
            dict: Dictionary met productinformatie
        """
        product_data = {}
        
        try:
            # Titel
            title_elem = await product_element.query_selector('.description .bold')
            if title_elem:
                product_data['titel'] = await title_elem.inner_text()
            else:
                product_data['titel'] = "Geen titel"
                
            # Prijs
            price_elem = await product_element.query_selector('.pricing .price')
            if price_elem:
                product_data['prijs'] = await price_elem.inner_text()
            else:
                product_data['prijs'] = "Prijs op aanvraag"
                
            # Garantie
            guarantee_elem = await product_element.query_selector('p:has-text("Garantie")')
            if guarantee_elem:
                text = await guarantee_elem.inner_text()
                product_data['garantie'] = text.replace('Garantie: ', '')
            else:
                product_data['garantie'] = "Onbekend"
                
            # Aanbieder
            supplier_elem = await product_element.query_selector('p:has-text("Aanbieder")')
            if supplier_elem:
                text = await supplier_elem.inner_text()
                product_data['aanbieder'] = text.replace('Aanbieder: ', '')
            else:
                product_data['aanbieder'] = "Onbekend"
                
            # Details
            detail_items = await product_element.query_selector_all('.description span.item')
            details = {}
            for item in detail_items:
                text = await item.inner_text()
                if ':' in text:
                    key, value = text.split(':', 1)
                    details[key.strip()] = value.strip()
            product_data['details'] = details
            
            # Afbeelding URL
            img_elem = await product_element.query_selector('img.img-responsive')
            if img_elem:
                product_data['afbeelding_url'] = await img_elem.get_attribute('src')
            else:
                product_data['afbeelding_url'] = "Geen afbeelding"
                
            # Timestamp
            product_data['scraped_at'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error scraping product info: {e}")
            
        return product_data
        
    async def scrape_category_with_pagination(self, category_url):
        """
        Scrape alle producten uit een categorie inclusief alle pagina's (Stap 3)
        
        Args:
            category_url (str): URL van de categorie
        """
        logger.info(f"Scraping category: {category_url}")
        
        # Navigeer naar de categorie
        await self.page.goto(category_url, wait_until='networkidle')
        
        page_number = 1
        
        while True:
            logger.info(f"Scraping page {page_number}")
            
            try:
                # Wacht tot de product lijst geladen is
                await self.page.wait_for_selector('#result-list', timeout=10000)
                
                # Kleine delay voor stabiliteit
                await asyncio.sleep(1)
                
                # Vind alle producten
                product_elements = await self.page.query_selector_all('ul#result-list > li')
                
                logger.info(f"Found {len(product_elements)} products on page {page_number}")
                
                # Scrape elk product
                for idx, product in enumerate(product_elements):
                    try:
                        product_info = await self.scrape_product_info(product)
                        product_info['pagina'] = page_number
                        product_info['categorie_url'] = category_url
                        self.products.append(product_info)
                    except Exception as e:
                        logger.warning(f"Error scraping product {idx}: {e}")
                        continue
                        
                # Zoek de "volgende" knop
                next_button = await self.page.query_selector('span.pagination input[value=">"]:not([disabled])')
                
                if next_button:
                    # Scroll naar de knop
                    await next_button.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    
                    # Klik op de volgende knop
                    await next_button.click()
                    
                    # Wacht tot de content is vernieuwd
                    await self.page.wait_for_load_state('networkidle')
                    
                    page_number += 1
                else:
                    logger.info("No more pages available")
                    break
                    
            except PlaywrightTimeout:
                logger.error(f"Timeout on page {page_number}")
                break
            except Exception as e:
                logger.error(f"Error on page {page_number}: {e}")
                break
                
        logger.info(f"Finished scraping category. Total products: {len(self.products)}")
        
    def save_to_csv(self, filename):
        """
        Sla de verzamelde producten op in een CSV bestand
        
        Args:
            filename (str): Naam van het output bestand
        """
        if not self.products:
            logger.warning("No products to save")
            return
            
        logger.info(f"Saving {len(self.products)} products to {filename}")
        
        # Bepaal alle mogelijke velden
        all_keys = set()
        for product in self.products:
            all_keys.update(product.keys())
            if 'details' in product:
                all_keys.update(f"detail_{k}" for k in product['details'].keys())
                
        # Verwijder 'details' uit de keys
        all_keys.discard('details')
        
        # Sorteer de velden
        fieldnames = sorted(all_keys)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in self.products:
                row = product.copy()
                
                # Pak details uit
                if 'details' in row:
                    details = row.pop('details')
                    for key, value in details.items():
                        row[f"detail_{key}"] = value
                        
                writer.writerow(row)
                
        logger.info(f"Successfully saved products to {filename}")
        
    async def scrape(self, license_plate, part_name, output_file=None):
        """
        Hoofdfunctie om het complete scraping proces uit te voeren
        
        Args:
            license_plate (str): Kenteken om te zoeken
            part_name (str): Naam van het onderdeel
            output_file (str): Output CSV bestandsnaam
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"onderdelenlijn_{license_plate}_{part_name}_{timestamp}.csv"
            
        try:
            # Setup browser
            await self.setup_browser()
            
            # Stap 1: Voer kenteken in
            await self.enter_license_plate(license_plate)
            
            # Stap 2: Vind categorie links
            category_links = await self.find_category_links(part_name)
            
            if not category_links:
                logger.warning(f"No categories found for part: {part_name}")
                return
                
            # Stap 3: Scrape elke categorie
            for idx, link in enumerate(category_links):
                logger.info(f"Processing category {idx + 1} of {len(category_links)}")
                await self.scrape_category_with_pagination(link)
                
            # Stap 4: Sla resultaten op
            self.save_to_csv(output_file)
            
            logger.info(f"Scraping completed successfully. Total products: {len(self.products)}")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise
        finally:
            await self.close_browser()


async def main():
    """Voorbeeld gebruik van de Playwright scraper"""
    # Configuratie
    LICENSE_PLATE = "27-XH-VX"
    PART_NAME = "Accubak"
    
    # Maak scraper instantie
    scraper = OnderdelenLijnScraperPlaywright(headless=False)
    
    # Start het scrapen
    await scraper.scrape(LICENSE_PLATE, PART_NAME)


if __name__ == "__main__":
    asyncio.run(main())