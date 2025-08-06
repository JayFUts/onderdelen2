# 🤖 AI Prijsanalyse Setup

## Functies

De AI-powered prijsanalyse biedt:

1. **Intelligente Prijsaanbevelingen** - Gebaseerd op marktdata en concurrentieanalyse
2. **Confidence Scores** - Hoge/Medium/Lage zekerheid per aanbeveling
3. **Marktpositionering** - Optimale prijsstrategie per productcategorie
4. **Instant Prijsadvies** - Direct advies per individueel product

## Setup

### Optie 1: Zonder OpenAI (Standaard)
De app werkt direct zonder extra configuratie. Je krijgt:
- Statistische prijsanalyse
- Marktgebaseerde aanbevelingen
- Confidence scores op basis van data

### Optie 2: Met OpenAI API (Geavanceerd)
Voor uitgebreide AI-analyse met natuurlijke taal:

1. **Verkrijg een OpenAI API Key**:
   - Ga naar [platform.openai.com](https://platform.openai.com)
   - Maak een account aan
   - Ga naar API Keys → Create new secret key

2. **Configureer de API Key**:
   
   **Voor lokaal gebruik:**
   ```bash
   export OPENAI_API_KEY="sk-your-api-key-here"
   python app.py
   ```
   
   **Voor Railway.app:**
   - Ga naar je Railway project
   - Settings → Variables
   - Add Variable: `OPENAI_API_KEY` = `sk-your-api-key-here`
   - Deploy zal automatisch herstarten

## Gebruik

### AI Prijsadvies Button
Na het scrapen zie je een nieuwe button: **"🤖 AI Prijsadvies"**

Dit geeft je:
- Prijsaanbevelingen per categorie
- Marktanalyse met reasoning
- Confidence indicatoren
- Geschatte winstmarges

### Features

1. **Categorie Analyse**
   - Gemiddelde marktprijzen
   - Optimale positionering
   - Concurrentie niveau

2. **Confidence Levels**
   - **Hoog**: Gebaseerd op exacte matches en voldoende data
   - **Medium**: Goede dataset maar geen exacte matches
   - **Laag**: Beperkte data beschikbaar

3. **Instant Prijsadvies**
   - Per product analyse
   - Direct toepasbaar
   - Marktcontext inclusief

## Kosten

### Zonder OpenAI
- **Gratis** - Gebruikt ingebouwde algoritmes

### Met OpenAI
- **GPT-3.5-turbo**: ~$0.002 per analyse
- **Geschat**: <$0.10 per 100 producten
- **Tip**: Monitor gebruik in OpenAI dashboard

## Best Practices

1. **Scrape eerst voldoende data** (min. 10-20 producten per categorie)
2. **Gebruik filters** voor specifieke categorieën
3. **Controleer confidence scores** bij prijsbeslissingen
4. **Test met kleine batches** eerst

## Troubleshooting

**"OpenAI API key niet geconfigureerd"**
- Voeg OPENAI_API_KEY toe als environment variable
- Herstart de applicatie

**"AI analyse mislukt"**
- Check API key geldigheid
- Controleer OpenAI account credits
- Probeer zonder API key (fallback mode)

**Lage confidence scores**
- Scrape meer producten
- Focus op specifieke categorieën
- Check voor exacte product matches