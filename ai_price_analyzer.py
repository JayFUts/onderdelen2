#!/usr/bin/env python3
"""
AI-powered price analysis using OpenAI API
"""

import os
import json
import logging
from typing import List, Dict, Any
import openai
from datetime import datetime

logger = logging.getLogger(__name__)

class AIPriceAnalyzer:
    """AI-gestuurde prijsanalyse met OpenAI"""
    
    def __init__(self, api_key: str = None):
        """
        Initialiseer de AI analyzer
        
        Args:
            api_key: OpenAI API key (of gebruik environment variable)
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        else:
            logger.warning("No OpenAI API key found - AI analysis will be disabled")
    
    def analyze_pricing(self, products: List[Dict[str, Any]], target_margin: float = 0.15) -> Dict[str, Any]:
        """
        Analyseer producten en geef AI-gestuurde prijsaanbevelingen
        
        Args:
            products: Lijst met product data
            target_margin: Gewenste winstmarge (default 15%)
            
        Returns:
            Dict met AI analyse en aanbevelingen
        """
        if not self.api_key:
            return {
                "error": "OpenAI API key niet geconfigureerd",
                "recommendations": []
            }
        
        try:
            # Bereid data voor voor AI analyse
            product_summary = self._prepare_product_summary(products)
            
            # Maak AI prompt
            prompt = self._create_analysis_prompt(product_summary, target_margin)
            
            # Vraag OpenAI om analyse
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Je bent een expert in automotive aftermarket pricing. Geef praktische prijsaanbevelingen in het Nederlands."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse de response
            ai_analysis = response.choices[0].message.content
            
            # Structureer de aanbevelingen
            recommendations = self._parse_recommendations(ai_analysis, products)
            
            return {
                "success": True,
                "analysis": ai_analysis,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {
                "error": f"AI analyse mislukt: {str(e)}",
                "recommendations": []
            }
    
    def _prepare_product_summary(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bereid product data voor voor AI analyse"""
        # Groepeer per categorie
        categories = {}
        for product in products:
            category = product.get('soort_onderdeel', 'Onbekend')
            if category not in categories:
                categories[category] = {
                    'products': [],
                    'price_range': {'min': float('inf'), 'max': 0},
                    'avg_price': 0
                }
            
            price = product.get('prijs_waarde', 0)
            if price > 0:
                categories[category]['products'].append({
                    'name': product.get('product_naam', ''),
                    'price': price,
                    'match_status': product.get('match_status', ''),
                    'specs': product.get('specifications', {})
                })
                categories[category]['price_range']['min'] = min(categories[category]['price_range']['min'], price)
                categories[category]['price_range']['max'] = max(categories[category]['price_range']['max'], price)
        
        # Bereken gemiddeldes
        for category in categories.values():
            if category['products']:
                category['avg_price'] = sum(p['price'] for p in category['products']) / len(category['products'])
        
        return categories
    
    def _create_analysis_prompt(self, product_summary: Dict[str, Any], target_margin: float) -> str:
        """Maak een gedetailleerde prompt voor OpenAI"""
        prompt = f"""Analyseer de volgende auto-onderdelen marktdata en geef prijsaanbevelingen:

MARKTDATA:
"""
        
        for category, data in product_summary.items():
            if data['products']:
                prompt += f"\n{category}:"
                prompt += f"\n- Aantal producten: {len(data['products'])}"
                prompt += f"\n- Prijsbereik: €{data['price_range']['min']:.2f} - €{data['price_range']['max']:.2f}"
                prompt += f"\n- Gemiddelde prijs: €{data['avg_price']:.2f}"
                
                # Voeg enkele voorbeelden toe
                examples = data['products'][:3]
                for ex in examples:
                    prompt += f"\n  • {ex['name']}: €{ex['price']:.2f} ({ex['match_status']})"
        
        prompt += f"""

OPDRACHT:
1. Analyseer de concurrentiepositie per productcategorie
2. Identificeer prijskansen (te hoog/laag geprijsde items)
3. Geef concrete prijsaanbevelingen met {target_margin*100:.0f}% marge
4. Overweeg kwaliteit indicatoren (100% match vs alternatief)
5. Geef strategisch advies voor maximale winst

Geef je analyse in een gestructureerd format met:
- Marktoverzicht
- Top 5 prijskansen
- Aanbevolen prijsstrategie per categorie
- Risico's en aandachtspunten
"""
        
        return prompt
    
    def _parse_recommendations(self, ai_analysis: str, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse AI aanbevelingen naar gestructureerde data"""
        recommendations = []
        
        # Basis aanbevelingen op prijsranges
        categories = {}
        for product in products:
            cat = product.get('soort_onderdeel', 'Onbekend')
            if cat not in categories:
                categories[cat] = []
            if product.get('prijs_waarde', 0) > 0:
                categories[cat].append(product)
        
        for category, cat_products in categories.items():
            if cat_products:
                prices = [p['prijs_waarde'] for p in cat_products]
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                
                # Bepaal optimale prijs op basis van marktpositie
                if len(prices) >= 3:
                    # Gebruik 25e percentiel voor competitieve pricing
                    sorted_prices = sorted(prices)
                    optimal_price = sorted_prices[len(sorted_prices)//4]
                else:
                    optimal_price = avg_price * 0.95  # 5% onder gemiddelde
                
                recommendations.append({
                    'category': category,
                    'current_avg': avg_price,
                    'suggested_price': optimal_price,
                    'potential_margin': (optimal_price - min_price) / optimal_price if optimal_price > 0 else 0,
                    'competition_level': 'Hoog' if len(prices) > 10 else 'Gemiddeld' if len(prices) > 5 else 'Laag',
                    'price_variance': (max_price - min_price) / avg_price if avg_price > 0 else 0
                })
        
        return recommendations
    
    def get_instant_price_recommendation(self, product: Dict[str, Any], competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Geef directe prijsaanbeveling voor een specifiek product
        
        Args:
            product: Het product om te prijzen
            competitors: Lijst met concurrerende producten
            
        Returns:
            Dict met prijsaanbeveling en onderbouwing
        """
        if not competitors:
            return {
                "recommended_price": 0,
                "confidence": "low",
                "reasoning": "Geen concurrentiedata beschikbaar"
            }
        
        # Analyseer concurrentie
        prices = [c['prijs_waarde'] for c in competitors if c.get('prijs_waarde', 0) > 0]
        
        if not prices:
            return {
                "recommended_price": 0,
                "confidence": "low",
                "reasoning": "Geen geldige prijzen gevonden"
            }
        
        # Bereken statistieken
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        # Match status weights
        exact_matches = [c['prijs_waarde'] for c in competitors 
                        if c.get('match_status') == '100% Match' and c.get('prijs_waarde', 0) > 0]
        
        if exact_matches:
            # Focus op exacte matches
            recommended = sum(exact_matches) / len(exact_matches) * 0.98  # 2% onder exacte matches
            confidence = "high"
            reasoning = f"Gebaseerd op {len(exact_matches)} exacte matches. Gem: €{sum(exact_matches)/len(exact_matches):.2f}"
        elif len(prices) >= 5:
            # Voldoende data voor percentiel strategie
            sorted_prices = sorted(prices)
            recommended = sorted_prices[len(sorted_prices)//3]  # 33e percentiel
            confidence = "medium"
            reasoning = f"Competitieve positie in markt van {len(prices)} producten. Range: €{min_price:.2f}-€{max_price:.2f}"
        else:
            # Weinig data
            recommended = avg_price * 0.95
            confidence = "low"
            reasoning = f"Beperkte data ({len(prices)} producten). Voorzichtige pricing onder gemiddelde"
        
        return {
            "recommended_price": round(recommended, 2),
            "confidence": confidence,
            "reasoning": reasoning,
            "market_analysis": {
                "competitors": len(prices),
                "avg_price": round(avg_price, 2),
                "price_range": f"€{min_price:.2f} - €{max_price:.2f}",
                "exact_matches": len(exact_matches)
            }
        }