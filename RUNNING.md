# MaapSetu Legal Metrology - Running & Deployment Guide

Welcome to the **MaapSetu** Legal Metrology compliance verification platform. This guide provides comprehensive, step-by-step instructions to set up, configure, run, test, and troubleshoot the entire system on a development or production machine.

---

## 1. Prerequisites

Ensure the following tools are installed on your workstation:

| Component | Minimum Version | Purpose |
| :--- | :--- | :--- |
| **Python** | 3.11+ | Django Backend, Rule Engine, OCR Microservice |
| **Node.js** | 18+ (LTS recommended) | Vite Frontend, React Officer & Citizen UI |
| **Docker & Docker Compose** | 20.10+ / v2 | PostgreSQL 16 database and Redis cache |
| **Ollama** | 0.3+ | Local zero-cost LLM for auxiliary semantic reasoning |
| **Ollama Model** | `llama3.2` | Structured JSON semantic compliance classification |

---

## 2. Initial Project Setup

### A. Clone and Open the Repository
```bash
git clone <repository_url>
cd SIH-2026
```

### B. Configure Environment Variables
Copy the sanitized environment template to `.env` in the repository root and `backend/`:
```bash
cp .env.example .env
cp .env.example backend/.env
```
*(On Windows PowerShell: `Copy-Item .env.example .env`)*

### C. Backend Virtual Environment & Dependencies
```bash
# From SIH-2026/backend:
python -m venv .venv

# Activate the virtual environment:
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Install backend dependencies:
pip install -r requirements/dev.txt
```

### D. Frontend Dependencies
```bash
# From SIH-2026/frontend:
npm install
```

### E. Start PostgreSQL Database
```bash
# From SIH-2026 root:
docker-compose up -d
```
Verify PostgreSQL is healthy:
```bash
docker ps
```
The container `legalmetro_db` will be running on port `5432`.

### F. Run Database Migrations & Seed Rules
```bash
cd backend
python manage.py migrate
python manage.py seed_rules
```

---

## 3. Ollama (Local Semantic LLM) Setup

MaapSetu uses **Ollama** running locally on port `11434` for zero-cost, privacy-preserving semantic validation (e.g. verifying ambiguous manufacturer addresses, generic commodity names, or consumer care contacts).

### A. Verify Ollama Installation
```bash
ollama --version
```

### B. Download the Required Model
```bash
ollama pull llama3.2
```

### C. Verify Installed Models
```bash
ollama list
```
Ensure `llama3.2:latest` is listed.

### D. Start the Ollama Daemon
```bash
ollama serve
```
*(If Ollama is already installed as a system tray/background service, it is accessible automatically at `http://localhost:11434`)*.

---

## 4. Multi-Terminal Execution Guide

To run the complete MaapSetu platform with all services active, open separate terminals for each subsystem:

### Terminal 1: Database & Cache (Docker)
```bash
cd SIH-2026
docker-compose up -d
```

### Terminal 2: Ollama LLM Service
```bash
ollama serve
```

### Terminal 3: OCR / Computer Vision Microservice (Port 8001)
```bash
cd SIH-2026/backend
# Ensure your virtual environment is active:
python ml_services/ocr_stub/main.py
```
*(Logs will indicate: `Uvicorn running on http://0.0.0.0:8001`)*

### Terminal 4: Django Backend Core (Port 8000)
```bash
cd SIH-2026/backend
# Bind to 0.0.0.0 to enable local network / mobile access:
python manage.py runserver 0.0.0.0:8000
```
*(Backend accessible at `http://localhost:8000/` and network IP)*

### Terminal 5: Frontend Vite Application (Port 5173)
```bash
cd SIH-2026/frontend
npm run dev
```
*(Vite dev server runs with `--host 0.0.0.0`, accessible at `http://localhost:5173` and network IP)*

---

## 5. Mobile Phone Testing & Inspection

You can use your mobile phone camera directly with MaapSetu's 6-panel guided capture workflow over your local Wi-Fi network.

1. **Ensure Mobile & PC are on the Same Wi-Fi Network**.
2. **Find Your Computer's Local IP Address**:
   - On Windows: Run `ipconfig` in PowerShell (look for `IPv4 Address` under your Wi-Fi adapter, e.g., `172.20.10.14`).
   - On Linux/macOS: Run `ifconfig` or `ip a` (e.g., `192.168.1.50`).
3. **Open the App on Your Phone**:
   - Open your mobile phone's browser (Chrome, Safari, Firefox).
   - Navigate to: **`http://<YOUR_PC_IP>:5173`** (e.g., `http://172.20.10.14:5173`).
4. **Proxy & API Connectivity**:
   - The Vite development server automatically proxies all `/api/...` and `/media/...` requests back to the Django backend on port `8000`. No manual CORS or backend URL changes are needed on the phone.

---

## 6. End-to-End Inspection Walkthrough

Follow these steps to complete a live package inspection from camera to report:

1. **Log In**:
   - Open the web application.
   - Use the demo officer account:
     - **Username**: `officer_demo`
     - **Password**: `demo1234`
2. **Navigate to Guided Capture**:
   - Go to **Field Officer Console** &rarr; **New Guided Inspection** (`/officer/capture/guided`).
3. **Execute 6-Panel Regulatory Capture**:
   - **Step 1**: Front Principal Display Panel (PDP) &rarr; Capture brand and product name.
   - **Step 2**: Mandatory Declaration Panel &rarr; Capture manufacturing date, batch, and consumer care.
   - **Step 3**: MRP & Net Quantity Close-Up &rarr; Focus on MRP statement and metric net quantity.
   - **Step 4**: Manufacturer & Packer Address &rarr; Capture physical registered address.
   - **Step 5**: Barcode & EAN/GTIN &rarr; Scan 13-digit GS1 barcode.
   - **Step 6**: Package Wrap-Around & Seal &rarr; Inspect package integrity and seals.
4. **Submit for Compliance Evaluation**:
   - Click **Submit Inspection**.
   - The system automatically:
     - Sends images to the OCR service (`/process`)
     - Normalizes raw OCR into Canonical Package Data
     - Evaluates 77 Legal Metrology rules deterministically
     - Dispatches semantic rules to Ollama LLM (`llama3.2`)
     - Generates the unified `ComplianceReport`
     - Persists records to PostgreSQL
5. **Review Compliance Finding**:
   - Inspect overall verdict: `COMPLIANT`, `NON_COMPLIANT`, or `NEEDS_REVIEW`.
   - Review rule-by-rule breakdowns, cited OCR evidence snippets, and confidence scores.

---

## 7. Testing & Quality Assurance

### Run Complete Backend Test Suite
```bash
cd SIH-2026/backend
python manage.py test tests
```
*Expected: 113 tests pass (`OK`), covering all deterministic, semantic, OCR, database, and integration cases.*

### Frontend Code Quality & Linting
```bash
cd SIH-2026/frontend
npm run lint
```
*Expected: 0 warnings and 0 errors (`oxlint`).*

### Frontend Production Build
```bash
cd SIH-2026/frontend
npm run build
```
*Expected: Compiles TypeScript (`tsc -b`) and generates production bundle via Vite.*

---

## 8. Troubleshooting & FAQ

### 1. PostgreSQL Connection Error (`could not connect to server`)
- **Cause**: The Docker database container is stopped or starting up.
- **Fix**: Run `docker-compose up -d` in `SIH-2026/` and check status with `docker ps`.

### 2. Ollama Unavailable / Connection Refused
- **Behavior**: Deterministic rules continue working normally; semantic rules gracefully downgrade to `REVIEW`. The app **never crashes**.
- **Fix**: Start the Ollama service by running `ollama serve` and verify with `curl http://localhost:11434/api/tags`.

### 3. OCR Service Returns 502 / Offline
- **Behavior**: If `OCR_USE_MOCK=False`, an `OCRServiceError` is logged.
- **Fix**: Start the OCR microservice via `python backend/ml_services/ocr_stub/main.py` on port 8001. For offline development without OCR, set `OCR_USE_MOCK=True` in `.env`.

### 4. Port Already in Use (e.g. 5173 or 8000)
- **Fix**:
  - For frontend: Run on another port if needed: `npx vite --host 0.0.0.0 --port 5174`
  - For backend: Kill the lingering Python process or specify a port: `python manage.py runserver 0.0.0.0:8002`

### 5. Camera Access Denied on Mobile Phone
- **Cause**: Mobile browsers restrict `navigator.mediaDevices.getUserMedia` on non-HTTPS origins unless accessed via `localhost` or configured as a secure development origin.
- **Fix**: In Chrome on Android, go to `chrome://flags/#unsafely-treat-insecure-origin-as-secure`, add `http://<YOUR_PC_IP>:5173`, enable the flag, and restart the browser. Or use the built-in "Upload Photo / Gallery Fallback" button on the capture screen.
