# CPL Cross Compiler — Flask Version

## Project Structure
```
CPL_Flask/
├── app.py              ← Flask server (sirf yahi chalana hai)
├── requirements.txt    ← Dependencies
└── templates/
    └── index.html      ← Pura UI yahan hai
```

## Step 1 — Python Install Karein (agar nahi hai)
https://python.org se Python 3.8+ download karein.
Check karo: `python --version`

## Step 2 — Flask Install Karein
Terminal/Command Prompt mein:

```
pip install flask
```

## Step 3 — App Run Karein
```
cd CPL_Flask
python app.py
```

Browser mein khulega: http://localhost:5000

## Step 4 — API Key Daalen
- Browser mein upar ek field milega: "Anthropic API Key"
- https://console.anthropic.com se apni key banayein
- Wahan paste karein aur Save dabayein
- Key browser mein save ho jaati hai (baar baar dalni nahi padegi)

## Note
- Node.js ki koi zaroorat nahi!
- Sirf Python + Flask chahiye
- Sab kuch ek file mein hai (templates/index.html)
