# 🛡️ Guardian Bot - Deployment Guide

## 🎉 NEW: Instagram Analytics & AI Features!

Guardian Bot artık **Instagram analytics** ve **AI-powered content management** özellikleriyle geliyor!

### 📱 Instagram Özellikleri:
- 🎯 **Profil Analizi** - Engagement, algoritma skoru, monetization
- 📊 **Performans Tahmini** - Monte Carlo simülasyonu ile reach/engagement tahmini
- ✍️ **AI Caption Üretici** - GPT-4/Claude/Gemini ile caption oluşturma
- #️⃣ **Hashtag Optimizasyonu** - 7+ kategori, trend analizi
- 🚀 **Büyüme Stratejisi** - Growth hacking planları
- 🎯 **Rakip Analizi** - Benchmarking ve competitive intelligence
- ⏰ **Optimal Zamanlama** - En iyi paylaşım saatleri
- 💰 **Monetization Hesaplayıcı** - Kazanç potansiyeli

**Detaylar için:** [INSTAGRAM_FEATURES.md](INSTAGRAM_FEATURES.md)

---

## Dosyalar
- `guardian_bot.py` - Tek dosya bot kodu
- `requirements.txt` - Python paketleri
- `Procfile` - Railway/Heroku için
- `runtime.txt` - Python versiyonu

## 🚀 Railway.app'e Yükleme (ÜCRETSİZ)

### 1. GitHub'a yükle
1. GitHub'da yeni repo oluştur
2. `deploy` klasöründeki dosyaları yükle

### 2. Railway.app
1. [railway.app](https://railway.app) adresine git
2. GitHub ile giriş yap
3. "New Project" → "Deploy from GitHub repo"
4. Repoyu seç

### 3. Environment Variables (Ortam Değişkenleri)
Railway'de Variables sekmesine git ve ekle:
```
DISCORD_TOKEN=senin_discord_token
GEMINI_API_KEY=senin_gemini_key
BOT_PREFIX=!
```

### 4. Deploy
Otomatik deploy olacak. Logs'dan takip et.

---

## 🎨 Render.com'a Yükleme (ÜCRETSİZ)

### 1. Render.com
1. [render.com](https://render.com) adresine git
2. GitHub ile giriş yap
3. "New" → "Background Worker"
4. GitHub repoyu bağla

### 2. Ayarlar
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python guardian_bot.py`

### 3. Environment Variables
Environment sekmesinden ekle:
```
DISCORD_TOKEN=senin_discord_token
GEMINI_API_KEY=senin_gemini_key
```

---

## 🔄 Replit'e Yükleme (ÜCRETSİZ)

### 1. Replit.com
1. [replit.com](https://replit.com) adresine git
2. "Create Repl" → "Import from GitHub"
3. Veya yeni Python repl oluştur ve dosyaları yapıştır

### 2. Secrets
Tools → Secrets'e git:
- `DISCORD_TOKEN` = token
- `GEMINI_API_KEY` = key

### 3. Run
"Run" butonuna bas!

### UptimeRobot ile 7/24 Çalıştırma
1. [uptimerobot.com](https://uptimerobot.com) hesabı aç
2. New Monitor → HTTP(s)
3. Replit URL'ini ekle
4. 5 dakikada bir ping atar, bot uyanık kalır

---

## ⚠️ Önemli Notlar

1. **Token Güvenliği**: Token'ı asla public repoya koyma!
2. **Ücretsiz Limitler**: 
   - Railway: Aylık 500 saat (yeterli)
   - Render: 750 saat
   - Replit: Sınırsız ama uyuyor (UptimeRobot gerekli)

3. **Veritabanı**: SQLite dosya olarak saklanır. Her deploy'da sıfırlanabilir.
   - Kalıcı için: PostgreSQL/MongoDB kullan (Railway ücretsiz veriyor)
