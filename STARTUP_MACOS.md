# 🚀 macOS Startup Guide

## Quick Fix - Use pip3 and python3

On macOS, use `pip3` and `python3` instead of `pip` and `python`

### Terminal 1 - Backend Setup & Run

```bash
cd "/Users/santhosh/Desktop/All Folders/autism-detector/backend"
pip3 install -r requirements.txt
python3 main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Terminal 2 - Frontend Setup & Run

```bash
cd "/Users/santhosh/Desktop/All Folders/autism-detector/frontend"
npm install
npm run dev
```

You should see:
```
VITE v5.0.0  ready in XXX ms
➜  Local:   http://localhost:3000/
```

### Open Browser

```
http://localhost:3000
```

---

## Optional: Create Aliases (Make it Easier)

Add these lines to your `~/.zshrc` or `~/.bash_profile`:

```bash
# Add these lines
alias python=python3
alias pip=pip3
```

Then reload:
```bash
source ~/.zshrc
# or
source ~/.bash_profile
```

After this you can use `python` and `pip` instead of `python3` and `pip3`

---

## Verify Installation

```bash
# Check Python
python3 --version          # Should show Python 3.14.3
pip3 --version             # Should show pip 26.0

# Check Node.js
node --version             # Should show v20.x.x
npm --version              # Should show 10.x.x
```

---

## Troubleshooting

### "python3: command not found"
```bash
# Install Python using Homebrew
brew install python3
```

### "pip3: command not found"
```bash
# Install pip (usually comes with Python)
python3 -m pip install --upgrade pip
```

### "npm: command not found"
```bash
# Install Node.js using Homebrew
brew install node
```

---

## Ready to Start!

Just follow the Terminal 1 and Terminal 2 commands above!
