# Railway.app Deployment Guide

## Quick Deploy

1. **Push to GitHub**: Zorg dat je code in een GitHub repository staat
2. **Connect Railway**: Ga naar [railway.app](https://railway.app) en connect je GitHub account
3. **Deploy**: Klik "New Project" → "Deploy from GitHub repo" → selecteer deze repo
4. **Wacht**: Railway bouwt automatisch de Docker container en deploy de applicatie

## Automatische Configuratie

Railway detecteert automatisch:
- `Dockerfile` voor container build
- `railway.json` voor deployment configuratie
- `requirements.txt` voor Python dependencies
- Poort via `$PORT` environment variable

## Na Deployment

1. **URL krijgen**: Railway geeft je een `xxx.railway.app` URL
2. **Custom domein** (optioneel): Voeg je eigen domein toe in Railway dashboard
3. **Monitoring**: Check logs in Railway dashboard voor debugging

## Belangrijke Opmerkingen

### Chrome & Selenium
- Chrome wordt automatisch geïnstalleerd in de container
- Scraper draait altijd in headless mode voor server performance
- WebDriver wordt automatisch gedownload bij eerste gebruik

### Prestaties
- Railway's gratis tier heeft beperkte resources
- Voor intensief scrapen: overweeg upgrade naar Pro plan
- Sessions worden opgeslagen in memory (niet persistent)

### Kosten
- **Gratis tier**: $5 gratis credits per maand
- **Pro plan**: $20/maand voor unlimited usage
- Scraping kan resources verbruiken, monitor je usage

## Troubleshooting

### Build Errors
```bash
# Check Railway build logs in dashboard
# Common issues:
# - Chrome installation failing
# - Memory limits during pip install
```

### Runtime Errors
```bash
# Check Railway deployment logs
# Common issues:
# - Chrome driver path issues (should auto-resolve)
# - Memory limits during scraping
# - Timeouts (increase in scraper settings)
```

### Performance Issues
- Reduce scraping concurrency
- Enable request delays
- Monitor Railway metrics

## Environment Variables

Railway automatisch ingestelde variabelen:
- `PORT`: Poort waarop de app draait
- `PYTHONUNBUFFERED`: Voor proper logging
- `FLASK_ENV`: Ingesteld op production

## Local Testing

Test de productie setup lokaal:

```bash
# Build Docker container
docker build -t onderdelenlijn-scraper .

# Run container
docker run -p 5000:5000 -e PORT=5000 onderdelenlijn-scraper

# Test op http://localhost:5000
```

## Database Persistence

Let op: Huidige setup gebruikt in-memory sessions. Voor productie met meerdere gebruikers, overweeg:
- Redis voor session storage
- Database voor scraped data persistence
- File storage voor CSV exports (Railway Volumes)

## Scaling

Voor grotere workloads:
- Enable Railway Pro plan
- Add Redis service voor shared sessions
- Consider worker processes voor background scraping
- Implement queue system voor large scraping jobs