# 🌿 Mimea Salama — AI Plant Disease Detection

AI-powered plant disease detection for East African farmers.
**Python + Flask · Groq AI (FREE) · English & Kiswahili · Deployable on Vercel**

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 AI Diagnosis | Detects 200+ plant diseases using Llama 4 via Groq |
| 🌍 Bilingual | Full English & Kiswahili support |
| 📱 Mobile Ready | Responsive design + camera capture |
| 🚫 Smart Validation | Rejects non-plant images automatically |
| 👤 Farmer Accounts | Register/login with phone + PIN |
| 📋 Scan History | Saves all scans with photos per farmer |
| 📊 Dashboard | Disease stats and charts |
| 🗺️ Disease Map | Plots scan locations on Kenya map |
| 📄 PDF Export | Download full scan report |
| 📲 WhatsApp Share | Share diagnosis instantly |
| 🗣️ Voice Output | Reads diagnosis aloud in Kiswahili/English |
| 🌐 Offline PWA | Works without internet, installs on phone |
| 🌦️ Weather Alerts | Disease risk based on local weather |
| 🔔 Notifications | Browser alerts for disease outbreaks |
| 🌱 Crop Calendar | Planting & care schedule for 5 crops |
| 🏪 Agro-dealer Locator | Find nearest shops for pesticides |
| 📞 Expert Hotline | One-tap call/WhatsApp to agronomist |
| 📚 Disease Encyclopedia | Offline guide to common plant diseases |

---

## 📁 Project Structure
```
mimea-salama/
├── app.py                  ← Flask backend (main server)
├── templates/
│   └── index.html          ← Frontend app (served by Flask)
├── static/
│   ├── sw.js               ← Service worker (offline PWA)
│   └── manifest.json       ← PWA manifest
├── requirements.txt        ← Python packages
├── vercel.json             ← Vercel deployment config
├── runtime.txt             ← Python version for Vercel
├── .env                    ← Your secret keys (NEVER commit)
├── .env.example            ← Safe template
├── .gitignore              ← Keeps .env off GitHub
└── README.md               ← This file
```

---

## 🔑 Step 1 — Get Your FREE Groq API Key

1. Go to **https://console.groq.com**
2. Sign up with your Google or GitHub account
3. Click **"API Keys"** → **"Create API Key"**
4. Copy the key — it starts with `gsk_...`
5. No credit card needed ✅
6. Free tier: **14,400 requests/day**

---

## 🚀 Step 2 — Local Setup in VSCode

### Open the project
```bash
code mimea-salama
```

### Create a virtual environment
In VSCode terminal (`Ctrl + `` ` ``):
```bash
python -m venv venv
```

Activate it:
- **Windows:**   `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

You'll see `(venv)` in the terminal ✅

### Install packages
```bash
pip install -r requirements.txt
```

### Add your API key
```bash
cp .env.example .env
```
Open `.env` and fill in your real key:
```
GROQ_API_KEY=gsk_YOUR-REAL-KEY-HERE
FLASK_ENV=development
SECRET_KEY=any-random-string-here
```

### Run the app
```bash
python app.py
```
Open **http://localhost:5000** 🎉

Check server health at **http://localhost:5000/health**

---

## 🌐 Step 3 — Deploy to Vercel (Free Hosting)

### Push to GitHub
```bash
git init
git add .
git commit -m "Launch Mimea Salama"
```
Go to **https://github.com/new** → Create repo `mimea-salama` → push.

### Deploy via Vercel website
1. Go to **https://vercel.com** → Sign up with GitHub
2. Click **"Add New Project"** → Import `mimea-salama`
3. Leave settings as default → click **"Deploy"**

### Add environment variables on Vercel
Go to your project → **Settings → Environment Variables** → add:

| Name | Value |
|---|---|
| `GROQ_API_KEY` | your Groq key |
| `SECRET_KEY` | any random string |
| `FLASK_ENV` | production |

Click **Save** → go to **Deployments** → **Redeploy**

Your app is live at **https://mimea-salama.vercel.app** 🌍

---

## ✅ Verify It's Working

Visit **http://localhost:5000/health**:
```json
{
  "status": "ok",
  "ai_backend": "Groq (llama-4-scout)",
  "free_tier": true,
  "api_key_configured": true,
  "message": "Mimea Salama backend is running 🌿"
}
```

---

## 📱 Install on Phone (PWA)

1. Open the app in Chrome on your phone
2. Tap the **"Add to Home Screen"** banner
3. The app installs like a native app
4. Works offline after first load ✅

---

## 💡 VSCode Tips

- Install **Python** extension (Microsoft) for syntax highlighting
- Install **Pylance** for smart autocomplete
- Press **F5** to run with the debugger
- `Ctrl + Shift + P` → **"Python: Select Interpreter"** → pick `venv`
- Install **Thunder Client** to test API routes

---

## 🔧 API Routes

| Method | Route | Description |
|---|---|---|
| GET | `/` | Serve the app |
| GET | `/health` | Server health check |
| POST | `/analyze` | Analyze plant image |
| POST | `/register` | Create farmer account |
| POST | `/login` | Login farmer |
| POST | `/logout` | Logout farmer |
| GET | `/me` | Current farmer info |
| GET | `/history` | Get scan history |
| DELETE | `/history/<id>` | Delete a scan |
| DELETE | `/history/clear` | Clear all scans |
| GET | `/stats` | Disease statistics |
| GET | `/map-data` | Scan GPS locations |
| POST | `/save-location` | Save scan GPS |
| GET | `/weather` | Weather + disease risk |
| GET | `/crops` | List of crops |
| GET | `/crop-calendar` | Crop calendar data |
| GET | `/agrodealers` | Nearest agro-dealers |
| GET | `/encyclopedia` | Disease encyclopedia |

---

## 💰 Groq Free Tier

| Metric | Free Limit |
|---|---|
| Requests per day | 14,400 |
| Requests per minute | 30 |
| Cost | $0.00 |

---

## 🗺️ Roadmap

- [ ] SMS fallback for non-smartphone users
- [ ] Community disease outbreak reports
- [ ] Farm progress tracker
- [ ] Marketplace for farmers
- [ ] NGO/Government admin dashboard
- [ ] More languages (Kikuyu, Luo, Kamba)

---

Built with ❤️ for East African farmers · Powered by Groq AI · Developed in Kenya 🇰🇪 by Meshack Muindi
