# 🚀 Railway.app Deployment Guide

## ⚠️ VEILIGHEID EERST
Je GitHub token was zichtbaar in de chat. Om veilig te deployen:

1. **Wijzig je GitHub token** in je GitHub settings:
   - Ga naar GitHub.com → Settings → Developer settings → Personal access tokens
   - Delete de huidige token (voor veiligheid)
   - Maak een nieuwe token aan

## 📤 Code naar GitHub pushen

Voer dit commando uit in je terminal:

```bash
./push_to_github.sh YOUR_NEW_GITHUB_TOKEN
```

Dit script zal:
- ✅ Veilig je code pushen naar GitHub
- ✅ Je token niet in de history opslaan
- ✅ Deployment instructies tonen

## 🌐 Railway.app Deployment

### Stap 1: Railway Account
1. Ga naar [railway.app](https://railway.app)
2. Klik "Login" → "GitHub"
3. Authorize Railway toegang tot je GitHub

### Stap 2: Project Aanmaken
1. Klik "New Project"
2. Selecteer "Deploy from GitHub repo"
3. Kies "JayFUts/onderdelen2"
4. Klik "Deploy Now"

### Stap 3: Wachten op Build
- ⏱️ Build tijd: ~5-10 minuten
- 🔍 Monitor progress in Railway dashboard
- 📋 Build logs tonen Chrome installatie progress

### Stap 4: URL Verkrijgen
- Railway geeft je automatisch een URL
- Format: `https://onderdelen2-production-xxxx.up.railway.app`
- URL is direct toegankelijk na succesvolle deploy

## 📊 Na Deployment

### ✅ Test de Applicatie
1. Open je Railway URL
2. Test kenteken invoer (bijv: 27-XH-VX)
3. Test onderdeel zoeken (bijv: Remschijf)
4. Verifieer prijsanalyse werkt

### 📈 Monitoring
- **Railway Dashboard**: Real-time metrics, logs, usage
- **Health Checks**: Automatische uptime monitoring
- **Performance**: CPU, memory, response times

### 💰 Kosten Bewaking
- **Gratis tier**: $5 credits/maand
- **Monitor usage** in Railway dashboard
- **Upgrade naar Pro** bij intensief gebruik

## 🛠️ Troubleshooting

### Common Issues:

**Build fails bij Chrome installatie:**
```
Solution: Wacht ~10 minuten - Chrome download kan traag zijn
Check: Railway build logs voor specifieke errors
```

**Memory errors tijdens scraping:**
```
Solution: Railway Pro plan voor meer memory
Alternative: Reduce scraping batch size
```

**Timeouts:**
```
Check: Network connectivity
Increase: Timeout values in scraper
Monitor: Railway performance metrics
```

### 🔧 Configuration Updates

Als je changes moet maken:
1. Update lokale code
2. `git add . && git commit -m "Update"`
3. `git push` (je remote is al geconfigureerd)
4. Railway auto-redeploys binnen ~2 minuten

## 🌟 Features Live op Railway

✅ **Web Dashboard** - Modern interface voor scraping
✅ **Real-time Progress** - Live scraping status updates  
✅ **Prijsanalyse** - Marktonderzoek per productcategorie
✅ **CSV Export** - Downloadbare resultaten
✅ **Multi-category Scraping** - Smart category selection
✅ **Concurrentieanalyse** - Pricing intelligence tool

## 📞 Support

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **GitHub Issues**: Voor code bugs/features
- **Railway Discord**: Voor deployment support

🎉 **Je scraper is nu live en beschikbaar wereldwijd via Railway!**