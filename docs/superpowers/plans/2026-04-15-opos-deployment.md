# OPOS Deployment Plan (Docker Compose)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the backend and frontend into a single `docker-compose.yml`, then deploy to the Oracle server with one command.

**Architecture:** Two containers — `backend` (FastAPI + uvicorn) and `frontend` (nginx serving built Vue SPA + proxying `/api/*` to backend). A `data/` bind mount holds SQLite, notes, and the PDF. The server exposes port 80 (HTTP — VPN encrypts transit).

**Tech Stack:** Docker, Docker Compose v2, Oracle Linux 8/9

**Prerequisites:**
- Backend plan complete (backend/Dockerfile working)
- Frontend plan complete (frontend/Dockerfile + nginx.conf working)
- Docker Desktop installed locally (Windows) for local testing
- Oracle server accessible via SSH

---

## File Structure

```
OPOS/                             ← project root (this plan's working dir)
├── docker-compose.yml            ← Task 1
├── .env                          ← Task 1 (GEMINI_API_KEY — never committed)
├── .env.example                  ← Task 1 (template)
├── .gitignore                    ← Task 1
├── data/                         ← Task 2 (bind-mounted volume)
│   ├── ApuntsTemari.md           ← copy from OPOS root
│   └── EdicteC1Maçanet.pdf       ← copy from OPOS root
├── backend/                      ← from backend plan
└── frontend/                     ← from frontend plan
```

---

## Task 1: docker-compose.yml + .env

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Create docker-compose.yml**

```yaml
services:
  backend:
    build: ./backend
    restart: unless-stopped
    env_file: .env
    environment:
      DB_PATH: /data/opos.db
      NOTES_PATH: /data/ApuntsTemari.md
      PDF_PATH: /data/EdicteC1Maçanet.pdf
    volumes:
      - ./data:/data
    networks:
      - opos-net
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - opos-net

networks:
  opos-net:
    driver: bridge
```

- [ ] **Step 2: Create .env.example**

```
GEMINI_API_KEY=your_gemini_api_key_here
```

- [ ] **Step 3: Create .gitignore at project root**

```
.env
data/opos.db
__pycache__/
*.pyc
node_modules/
frontend/dist/
backend/venv/
backend/opos.db
```

- [ ] **Step 4: Verify docker-compose.yml syntax**

```bash
docker compose config
```
Expected: prints the resolved config with no errors.

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml .env.example .gitignore
git commit -m "feat: docker-compose.yml with backend + frontend services"
```

---

## Task 2: Data Volume + Local Test

**Files:**
- Create: `data/` directory
- Copy: `ApuntsTemari.md` and `EdicteC1Maçanet.pdf` into `data/`

- [ ] **Step 1: Create data directory and copy files**

```bash
# From the OPOS project root (Windows):
mkdir data

# Copy the notes and PDF into the data volume:
copy "ApuntsTemari.md" data\
copy "EdicteC1Maçanet.pdf" data\
```

Verify:
```bash
dir data\
```
Expected: `ApuntsTemari.md` and `EdicteC1Maçanet.pdf` present.

- [ ] **Step 2: Create .env with real API key**

```bash
# Create .env (NOT committed — already in .gitignore):
echo GEMINI_API_KEY=your_actual_key_here > .env
```

Edit `.env` to put your actual Gemini API key (get from Google AI Studio).

- [ ] **Step 3: Build both images locally**

```bash
docker compose build
```
Expected: both `opos-backend` and `opos-frontend` build successfully. No errors.

If backend build fails with PyMuPDF issues on Windows:

```bash
# Add this to backend/requirements.txt instead of pymupdf:
# PyMuPDF==1.24.5
# The linux/amd64 Docker image handles this fine even on Windows ARM
docker compose build --no-cache backend
```

- [ ] **Step 4: Start locally and smoke test**

```bash
docker compose up -d
```
Expected: both containers start. Check:
```bash
docker compose ps
```
Expected:
```
NAME                STATUS
opos-backend-1      running (healthy)
opos-frontend-1     running
```

- [ ] **Step 5: Verify the app is accessible**

```bash
# Health (directly to backend)
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/health').read())"
# Expected: b'{"status":"ok"}'

# Through nginx (full stack)
curl http://localhost/api/health
# Expected: {"status":"ok"}

curl http://localhost/api/topics | python -m json.tool | head -15
# Expected: JSON array of 20 topics

# SPA loads
curl -s http://localhost/ | grep -c '<div id="app">'
# Expected: 1
```

- [ ] **Step 6: Stop local containers**

```bash
docker compose down
```

- [ ] **Step 7: Commit data setup**

```bash
git add data/.gitkeep  # keep data dir in git but not its contents
git commit -m "feat: data volume directory with gitkeep"
```

Note: add `data/*.md` and `data/*.pdf` to `.gitignore` if you don't want the notes committed.

---

## Task 3: Deploy to Oracle Server

- [ ] **Step 1: Install Docker on Oracle Linux**

SSH into the Oracle server:
```bash
ssh user@YOUR_SERVER_IP
```

Install Docker:
```bash
sudo dnf install -y dnf-utils
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Log out and back in for the group change to take effect, then verify:
```bash
docker --version
docker compose version
```
Expected: Docker 24.x+ and Docker Compose 2.x+

- [ ] **Step 2: Copy project files to server**

From Windows (PowerShell or WSL):
```powershell
# Copy the entire project (excluding .env — you'll create it on the server):
scp -r "C:\Users\iruiz\OneDrive - Sa Palomera\OTRAS COSAS\OPOS\backend" user@SERVER_IP:~/opos/
scp -r "C:\Users\iruiz\OneDrive - Sa Palomera\OTRAS COSAS\OPOS\frontend" user@SERVER_IP:~/opos/
scp "C:\Users\iruiz\OneDrive - Sa Palomera\OTRAS COSAS\OPOS\docker-compose.yml" user@SERVER_IP:~/opos/
scp "C:\Users\iruiz\OneDrive - Sa Palomera\OTRAS COSAS\OPOS\.env.example" user@SERVER_IP:~/opos/
scp "C:\Users\iruiz\OneDrive - Sa Palomera\OTRAS COSAS\OPOS\data\ApuntsTemari.md" user@SERVER_IP:~/opos/data/
scp "C:\Users\iruiz\OneDrive - Sa Palomera\OTRAS COSAS\OPOS\data\EdicteC1Macaçanet.pdf" user@SERVER_IP:~/opos/data/
```

Alternatively, use `git push` + `git clone` on the server (faster for code, still need scp for data files).

- [ ] **Step 3: Create .env on the server**

```bash
# On the Oracle server:
cd ~/opos
cp .env.example .env
nano .env  # Add: GEMINI_API_KEY=your_actual_key_here
chmod 600 .env
```

- [ ] **Step 4: Open firewall port 80**

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
sudo firewall-cmd --list-services
```
Expected: `http` in the list.

If using Oracle Cloud security lists: also open TCP port 80 ingress in the OCI console for the subnet.

- [ ] **Step 5: Build and start on server**

```bash
cd ~/opos
docker compose build
docker compose up -d
```
Expected: both containers start healthy.

```bash
docker compose ps
```
Expected: both services `running`.

- [ ] **Step 6: Verify from the server**

```bash
curl http://localhost/api/health
# Expected: {"status":"ok"}

curl http://localhost/api/topics | python3 -m json.tool | head -15
# Expected: 20 topics

curl -s http://localhost/ | grep -c 'id="app"'
# Expected: 1
```

---

## Task 4: End-to-End Mobile Test

- [ ] **Step 1: Get server IP for VPN access**

```bash
ip addr show | grep "inet " | grep -v 127
```
Note the private IP (e.g., `10.0.0.5`).

- [ ] **Step 2: Test from mobile (on VPN)**

1. Connect to VPN on mobile
2. Open browser → `http://10.0.0.5`
3. The OPOS app should load — no SSL warning (plain HTTP, VPN encrypts)

- [ ] **Step 3: Full golden-path test on mobile**

1. **Apunts:** Open drawer → select Tema 1 → content loads → select text → pick highlight color → switch to Dibuix → draw → tap save
2. **Flash:** Select topic → "Generar amb IA" → 15 cards appear → tap to flip → mark Sabia/No sabia
3. **Pràctica:** Select topic → Test → 10 questions → finish → score saved
4. **Progrés:** Shows updated % → "Analitzar amb IA" → readiness report with exam date badge

- [ ] **Step 4: Verify data persists**

```bash
# Check SQLite has data after mobile session:
docker compose exec backend python3 -c "
import sqlite3
conn = sqlite3.connect('/data/opos.db')
print('Sessions:', conn.execute('SELECT COUNT(*) FROM practice_sessions').fetchone()[0])
print('Annotations:', conn.execute('SELECT COUNT(*) FROM annotations').fetchone()[0])
conn.close()
"
```
Expected: counts > 0 reflecting your mobile session.

---

## Quick Reference: Operations

```bash
# Start everything:
docker compose up -d

# Stop everything:
docker compose down

# View logs:
docker compose logs -f

# Redeploy after backend code change:
docker compose build backend && docker compose up -d backend

# Redeploy after frontend code change:
docker compose build frontend && docker compose up -d frontend

# Check SQLite directly:
docker compose exec backend sqlite3 /data/opos.db ".tables"
docker compose exec backend sqlite3 /data/opos.db "SELECT topic_id, overall_pct FROM progress;"

# Restart a single service:
docker compose restart backend
```
