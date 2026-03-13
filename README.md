# 🌿 Mimea Salama — Python/Flask + Gemini (FREE)

AI plant disease detection with Swahili support.
Python + Flask backend · **Google Gemini (free tier)** · Deployable on Vercel.
**No credit card needed · 1,500 free requests/day**

---

## 📁 Project Structure

```
mimea-salama/
├── app.py               ← Flask backend (talks to Gemini)
├── templates/
│   └── index.html       ← The app frontend (served by Flask)
├── static/              ← Put images/icons here if needed
├── requirements.txt     ← Python packages
├── vercel.json          ← Vercel deployment config
├── .env                 ← Your secret Gemini key (NEVER commit this)
├── .env.example         ← Safe template
├── .gitignore           ← Keeps .env off GitHub
└── README.md            ← This file
```

---

## 🔑 Step 1 — Get Your FREE Gemini API Key

1. Go to **https://aistudio.google.com**
2. Sign in with your Google account
3. Click **"Get API Key"** → **"Create API key"**
4. Copy the key — it starts with `AIza...`
5. No credit card, no billing setup needed ✅

---

## 🚀 Step 2 — Local Setup in VSCode

### Open the project
```bash
code mimea-salama
```

### Create a virtual environment
In the VSCode terminal (`Ctrl + `` ` ``):
```bash
python -m venv venv
```
Activate it:
- **Windows:**   `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

You'll see `(venv)` in the terminal — that means it's active.

### Install packages
```bash
pip install -r requirements.txt
```

### Add your Gemini key
```bash
cp .env.example .env
```
Open `.env` and replace `your-gemini-key-here` with your real key:
```
GEMINI_API_KEY=AIzaYOUR-REAL-KEY-HERE
FLASK_ENV=development
```

### Run the app
```bash
python app.py
```
Open **http://localhost:5000** — fully working! 🎉

Check the server health at **http://localhost:5000/health**

---

## 🌐 Step 3 — Deploy to Vercel (Free Hosting)

### Install Vercel CLI
```bash
npm install -g vercel
```

### Push to GitHub first
```bash
git init
git add .
git commit -m "Launch Mimea Salama"
```
Go to https://github.com → New Repository → `mimea-salama`
Follow GitHub's push instructions.

### Deploy
```bash
vercel --prod
```

### Add your Gemini key to Vercel
```bash
vercel env add GEMINI_API_KEY
# Paste your key → press A to select all environments → Enter
```

### Redeploy
```bash
vercel --prod
```
Live at **https://mimea-salama.vercel.app** 🌍

---

## ✅ Verify It's Working

Visit http://localhost:5000/health and you should see:
```json
{
  "status": "ok",
  "ai_backend": "Google Gemini (gemini-1.5-flash)",
  "free_tier": true,
  "api_key_configured": true,
  "message": "Mimea Salama backend is running 🌿"
}
```

---

## 💡 VSCode Tips

- Install the **Python** extension (Microsoft) for syntax highlighting
- Install **Pylance** for smart autocomplete
- Press **F5** to run with the debugger
- `Ctrl + Shift + P` → "Python: Select Interpreter" → pick your `venv`

---

## 💰 Gemini Free Tier Limits

| Metric | Free Limit |
|--------|-----------|
| Requests per day | 1,500 |
| Requests per minute | 15 |
| Cost | $0.00 |

More than enough for a science fair or small farming community!

---

Built with ❤️ for East African farmers · Powered by Google Gemini AI
