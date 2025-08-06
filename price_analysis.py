#!/usr/bin/env python3
"""
Prijsanalyse module voor marktonderzoek en concurrentieanalyse
Helpt bij het bepalen van concurrerende prijzen voor auto-onderdelen
"""

import statistics
from collections import defaultdict
import re


class PriceAnalyzer:
    """Analyseert prijzen van geschrapte producten voor marktonderzoek"""
    
    def __init__(self, products):
        """
        Initialize met lijst van product dictionaries
        
        Args:
            products (list): Lijst van product dictionaries met prijs informatie
        """
        self.products = products
        self.price_data = self._extract_price_data()
    
    def _extract_price_data(self):
        """Extract en clean price data van alle producten"""
        price_data = []
        
        for product in self.products:
            price_info = {
                'product_id': product.get('product_id', 'Onbekend'),
                'titel': product.get('titel', 'Onbekend'),
                'soort_onderdeel': product.get('soort_onderdeel', 'Onbekend'),
                'prijs_text': product.get('prijs', ''),
                'prijs_numeriek': product.get('prijs_numeriek', 0.0),
                'prijs_type': product.get('prijs_type', 'Onbekend'),
                'aanbieder': product.get('aanbieder', 'Onbekend'),
                'match_kleur': product.get('match_kleur', 'unknown'),
                'direct_bestelbaar': product.get('direct_bestelbaar', False),
                'bouwjaar': None,
                'merk_onderdeel': None,
                'conditie': 'Onbekend'
            }
            
            # Extract specificaties voor betere analyse
            specs = product.get('specificaties', {})
            price_info['bouwjaar'] = specs.get('Bouwjaar')
            price_info['merk_onderdeel'] = specs.get('Merk onderdeel')
            
            # Bepaal conditie (Nieuw/Gebruikt)
            if 'nieuwe' in price_info['soort_onderdeel'].lower():
                price_info['conditie'] = 'Nieuw'
            elif 'gebruikte' in price_info['soort_onderdeel'].lower():
                price_info['conditie'] = 'Gebruikt'
                
            # Only include products met geldige prijzen
            if price_info['prijs_numeriek'] > 0:
                price_data.append(price_info)
                
        return price_data
    
    def get_overall_statistics(self):
        """Krijg overall prijsstatistieken"""
        if not self.price_data:
            return {}
            
        prices = [item['prijs_numeriek'] for item in self.price_data]
        
        return {
            'totaal_producten': len(self.price_data),
            'producten_met_prijs': len(prices),
            'gemiddelde_prijs': round(statistics.mean(prices), 2),
            'mediaan_prijs': round(statistics.median(prices), 2),
            'minimum_prijs': min(prices),
            'maximum_prijs': max(prices),
            'prijs_spreiding': round(max(prices) - min(prices), 2)
        }
    
    def get_price_distribution(self, num_buckets=5):
        """Krijg prijsverdeling in buckets voor histogram"""
        if not self.price_data:
            return []
            
        prices = [item['prijs_numeriek'] for item in self.price_data]
        min_price = min(prices)
        max_price = max(prices)
        bucket_size = (max_price - min_price) / num_buckets
        
        buckets = []
        for i in range(num_buckets):
            bucket_min = min_price + (i * bucket_size)
            bucket_max = min_price + ((i + 1) * bucket_size)
            
            count = sum(1 for price in prices if bucket_min <= price < bucket_max)
            if i == num_buckets - 1:  # Include max in last bucket
                count = sum(1 for price in prices if bucket_min <= price <= bucket_max)
                
            buckets.append({
                'range': f"€{bucket_min:.0f} - €{bucket_max:.0f}",
                'count': count,
                'percentage': round((count / len(prices)) * 100, 1)
            })
            
        return buckets
    
    def get_condition_analysis(self):
        """Analyseer prijzen per conditie (Nieuw vs Gebruikt)"""
        condition_stats = defaultdict(list)
        
        for item in self.price_data:
            condition_stats[item['conditie']].append(item['prijs_numeriek'])
            
        results = {}
        for condition, prices in condition_stats.items():
            if prices:
                results[condition] = {
                    'count': len(prices),
                    'gemiddelde': round(statistics.mean(prices), 2),
                    'mediaan': round(statistics.median(prices), 2),
                    'minimum': min(prices),
                    'maximum': max(prices)
                }
                
        return results
    
    def get_supplier_analysis(self):
        """Analyseer prijzen per aanbieder"""
        supplier_stats = defaultdict(list)
        
        for item in self.price_data:
            supplier_stats[item['aanbieder']].append(item['prijs_numeriek'])
            
        results = []
        for supplier, prices in supplier_stats.items():
            if prices and len(prices) >= 2:  # Only suppliers with 2+ products
                results.append({
                    'aanbieder': supplier,
                    'aantal_producten': len(prices),
                    'gemiddelde_prijs': round(statistics.mean(prices), 2),
                    'laagste_prijs': min(prices),
                    'hoogste_prijs': max(prices)
                })
                
        # Sort by aantal producten
        return sorted(results, key=lambda x: x['aantal_producten'], reverse=True)
    
    def get_match_quality_analysis(self):
        """Analyseer prijzen per match kwaliteit (groen/oranje/rood)"""
        match_stats = defaultdict(list)
        
        for item in self.price_data:
            match_stats[item['match_kleur']].append(item['prijs_numeriek'])
            
        results = {}
        match_labels = {
            'green': 'Perfecte match (groen)',
            'orange': 'Goede match (oranje)', 
            'red': 'Basis match (rood)',
            'unknown': 'Onbekend'
        }
        
        for match_color, prices in match_stats.items():
            if prices:
                results[match_labels.get(match_color, match_color)] = {
                    'count': len(prices),
                    'gemiddelde': round(statistics.mean(prices), 2),
                    'mediaan': round(statistics.median(prices), 2)
                }
                
        return results
    
    def get_price_recommendations(self):
        """Krijg prijsaanbevelingen gebaseerd op marktanalyse"""
        if not self.price_data:
            return {}
            
        stats = self.get_overall_statistics()
        condition_stats = self.get_condition_analysis()
        
        recommendations = {
            'conservatief': {
                'beschrijving': 'Veilige prijs onder marktgemiddelde',
                'prijs': round(stats['mediaan_prijs'] * 0.85, 2),
                'rationale': f"15% onder mediaan van €{stats['mediaan_prijs']}"
            },
            'marktconform': {
                'beschrijving': 'Prijs conform marktgemiddelde', 
                'prijs': stats['mediaan_prijs'],
                'rationale': f"Mediaan marktprijs van {len(self.price_data)} producten"
            },
            'premium': {
                'beschrijving': 'Hogere prijs voor kwaliteit/service',
                'prijs': round(stats['mediaan_prijs'] * 1.25, 2),
                'rationale': f"25% boven mediaan voor toegevoegde waarde"
            }
        }
        
        # Specifieke aanbevelingen per conditie
        if 'Gebruikt' in condition_stats:
            recommendations['gebruikt_marktprijs'] = {
                'beschrijving': 'Marktprijs voor gebruikte onderdelen',
                'prijs': condition_stats['Gebruikt']['mediaan'],
                'rationale': f"Mediaan van {condition_stats['Gebruikt']['count']} gebruikte onderdelen"
            }
            
        if 'Nieuw' in condition_stats:
            recommendations['nieuw_marktprijs'] = {
                'beschrijving': 'Marktprijs voor nieuwe onderdelen', 
                'prijs': condition_stats['Nieuw']['mediaan'],
                'rationale': f"Mediaan van {condition_stats['Nieuw']['count']} nieuwe onderdelen"
            }
            
        return recommendations
    
    def get_competitive_products(self, target_price=None, margin=0.1):
        """Vind concurrerende producten binnen een prijsrange"""
        if not target_price:
            stats = self.get_overall_statistics()
            target_price = stats['mediaan_prijs']
            
        price_min = target_price * (1 - margin)
        price_max = target_price * (1 + margin)
        
        competing_products = [
            item for item in self.price_data 
            if price_min <= item['prijs_numeriek'] <= price_max
        ]
        
        return sorted(competing_products, key=lambda x: x['prijs_numeriek'])
    
    def get_product_categories(self):
        """Krijg alle unieke productcategorieën"""
        categories = set()
        for product in self.price_data:
            category = product.get('soort_onderdeel', 'Onbekend')
            if category and category != 'Onbekend':
                categories.add(category)
        return sorted(list(categories))
    
    def get_category_summary(self):
        """Krijg samenvatting van alle categorieën met product counts"""
        category_counts = defaultdict(int)
        category_prices = defaultdict(list)
        
        for product in self.price_data:
            category = product.get('soort_onderdeel', 'Onbekend')
            category_counts[category] += 1
            if product['prijs_numeriek'] > 0:
                category_prices[category].append(product['prijs_numeriek'])
        
        summary = []
        for category, count in category_counts.items():
            prices = category_prices.get(category, [])
            avg_price = sum(prices) / len(prices) if prices else 0
            
            summary.append({
                'categorie': category,
                'totaal_producten': count,
                'producten_met_prijs': len(prices),
                'gemiddelde_prijs': round(avg_price, 2) if avg_price > 0 else None
            })
        
        return sorted(summary, key=lambda x: x['totaal_producten'], reverse=True)
    
    def filter_by_category(self, category):
        """Filter producten op specifieke categorie en return nieuwe analyzer"""
        filtered_products = [
            product for product in self.products 
            if product.get('soort_onderdeel', '').lower() == category.lower()
        ]
        return PriceAnalyzer(filtered_products)
    
    def generate_market_report(self, category=None):
        """Genereer volledig marktrapport, optioneel gefilterd op categorie"""
        if category:
            analyzer = self.filter_by_category(category)
            report = {
                'categorie': category,
                'samenvatting': analyzer.get_overall_statistics(),
                'prijsverdeling': analyzer.get_price_distribution(),
                'conditie_analyse': analyzer.get_condition_analysis(),
                'aanbieder_analyse': analyzer.get_supplier_analysis()[:10],
                'match_analyse': analyzer.get_match_quality_analysis(),
                'prijsaanbevelingen': analyzer.get_price_recommendations(),
                'alle_categorieën': self.get_category_summary(),
                'gegenereerd_op': None
            }
        else:
            report = {
                'samenvatting': self.get_overall_statistics(),
                'prijsverdeling': self.get_price_distribution(),
                'conditie_analyse': self.get_condition_analysis(),
                'aanbieder_analyse': self.get_supplier_analysis()[:10],
                'match_analyse': self.get_match_quality_analysis(),
                'prijsaanbevelingen': self.get_price_recommendations(),
                'alle_categorieën': self.get_category_summary(),
                'gegenereerd_op': None
            }
        
        return report