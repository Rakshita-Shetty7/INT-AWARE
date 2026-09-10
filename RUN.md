# ▶ HOW TO RUN THIS PROJECT — START HERE

This guide assumes **nothing**. Follow it top to bottom. It tells you exactly
**where to go** and **what to type**.

There are two ways to run the system. **Use Way 1 (Docker).** It starts the whole
system — database, honeypot, backend, and dashboard — with a single command.
Way 2 (manual) is only if you want to edit code live.

---

## What you need installed (one time)

| Tool | Why | Get it |
|---|---|---|
| **Docker Desktop** | Runs the whole system | https://www.docker.com/products/docker-desktop/ → install → **launch it** → wait until the whale icon says **"Engine running"** |
| **Python 3.12+** | Only to run the test-attack script | https://www.python.org/downloads/ → during install, tick **"Add Python to PATH"** |

> You do **not** need to install MongoDB, Node.js, or Cowrie yourself — Docker
> brings all of those inside containers.

---

# ✅ WAY 1 — Run with Docker (recommended)

### Step 1 — Open a terminal **inside the project folder**

1. Open **File Explorer**.
2. Go to the project folder:
   `C:\Users\raksh\OneDrive\Desktop\INT-AWARE`
3. Click the **address bar** at the top, type `cmd`, and press **Enter**.
   A black terminal window opens, already "inside" the project folder.

> ✔️ You're in the right place if the terminal prompt ends with `...\INT-AWARE>`.

### Step 2 — Create your settings file (first time only)

```bash
copy .env.example .env
```

That's enough to run. (Optional: open `.env` in Notepad and paste a
`GEMINI_API_KEY` if you have one — **the system works fully without it.**)

### Step 3 — Start the whole system

```bash
docker compose up -d --build
```

The **first** time this takes ~2–4 minutes (it downloads and builds everything).
Later starts take a few seconds. When it finishes you'll see `Started` next to
`mongo`, `cowrie`, `api`, and `dashboard`.

### Step 4 — Open the dashboard

Open your browser to:

- **Dashboard:** http://127.0.0.1:5173
- **API + interactive docs:** http://127.0.0.1:8000/docs

The dashboard will be up but mostly empty until you send some test attacks →

### Step 5 — Send test attacks so the dashboard fills with data

The system is a honeypot — it only shows data once someone "attacks" it. A safe
script does this for you (it types fake attacker commands into the **isolated**
honeypot; nothing runs on your PC). Do this **once** to set up the helper:

```bash
python -m venv .venv
```

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then run the attack simulation (drives **all 10 intent types** through the pipeline):

```bash
.venv\Scripts\python.exe scripts/demo_all_intents.py
```

Now **refresh the dashboard** — you'll see sessions, classified intents, risk
scores, and attacker profiles appear.

### Step 6 — Prove it's really working (optional but nice)

```bash
.venv\Scripts\python.exe scripts/verify_live.py
```

This reads the live API and prints a **PASS/FAIL** verdict, confirming the ML
model is classifying real events (each command labelled `ML` or `HYBRID`).

### Step 7 — Stop it when you're done

```bash
docker compose down
```

To wipe all captured data and start clean, add `-v`:

```bash
docker compose down -v
```

---

# 🛠️ WAY 2 — Run manually (only for live code editing)

Use this if you're changing the code and want instant reload. You need
**Python 3.12+**, **Node.js 18+**, and **MongoDB** running locally.

Open **four** terminals in `C:\Users\raksh\OneDrive\Desktop\INT-AWARE`.

**Terminal 1 — one-time setup:**
```bash
python -m venv .venv
```
```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```
```bash
copy .env.example .env
```

**Terminal 1 — start the honeypot (port 2222):**
```bash
.venv\Scripts\python.exe scripts/run_cowrie.py
```

**Terminal 2 — start the backend + pipeline (port 8000):**
```bash
.venv\Scripts\python.exe scripts/run_backend.py --host 127.0.0.1 --port 8000 --with-pipeline
```

**Terminal 3 — start the dashboard (port 5173):**
```bash
cd frontend
```
```bash
npm install
```
```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

**Terminal 4 — send test attacks & verify:**
```bash
.venv\Scripts\python.exe scripts/demo_all_intents.py
```
```bash
.venv\Scripts\python.exe scripts/verify_live.py
```

Open http://127.0.0.1:5173.

---

## If something goes wrong

| Symptom | Fix |
|---|---|
| `docker: command not found` / `Cannot connect to the Docker daemon` | Docker Desktop isn't running. Launch it, wait for **"Engine running"**, retry. |
| Dashboard loads but says "Unable to connect to backend" | Give it 10–20 s after `docker compose up`; the backend needs a moment. Then refresh. |
| Dashboard is empty | You haven't sent traffic yet — do **Step 5**. |
| `python: command not found` | Python isn't on PATH. Reinstall Python and tick **"Add Python to PATH"**, or use the full path `C:\...\python.exe`. |
| Port already in use (5173 / 8000 / 2222) | Something else is using it. `docker compose down`, close other apps on that port, retry. |
| Want to see what's running | `docker compose ps` |
| Want to read logs | `docker compose logs -f api` (or `dashboard`, `cowrie`, `mongo`) |

---

## What each address is

| URL | What it is |
|---|---|
| http://127.0.0.1:5173 | The analyst **dashboard** (what you look at) |
| http://127.0.0.1:8000/docs | The **API** with interactive docs |
| 127.0.0.1:2222 | The **honeypot** (attackers "connect" here; safe/emulated) |

> **Safety:** The honeypot only *emulates* a shell — no attacker command ever
> executes on your machine. Test attacks use documentation IP ranges that route
> nowhere. See the security notes in [`README.md`](README.md).
