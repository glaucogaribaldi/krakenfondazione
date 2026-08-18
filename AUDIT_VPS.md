# TECHNICAL AUDIT REPORT — VPS STATUS
## *krakenfondazione — Dual-Orbit V8.0 Real-time System Audit*

**Data dell'Audit:** Martedì 18 Agosto 2026  
**Ora dell'Audit:** 08:50 (Europe/Rome) / 06:50 UTC  
**Operatore AI:** TRE (Control Plane: Zava U50)  
**Host Destinatario:** `instance-20260719-152821` (Tailscale IP: `100.73.54.72`)

---

## 1. STATO DELLE RISORSE DI SISTEMA (HARDWARE & OS)
*   **Sistema Operativo:** Debian 13 (trixie) x86_64
*   **Kernel:** Linux 6.1.0-xx
*   **Uptime:** 6 giorni, 12 ore e 40 minuti
*   **Spazio Disco (`df -h /`):**
    *   Dimensione Totale: **252 GB**
    *   Spazio Usato: **45 GB** (19%)
    *   Spazio Disponibile: **197 GB** (81%)
    *   *Stato di Salute:* **Estremamente Sano** (Ampio margine per log SQLite WAL e record vettoriali).
*   **Carico di Lavoro CPU (`uptime`):**
    *   Load Average (1m, 5m, 15m): **`0.09`**, **`0.15`**, **`0.16`**
    *   *Stato di Salute:* **Ottimo**. La macchina lavora sotto la soglia di stress.

---

## 2. STATO DEI SERVIZI DI RETE & PORTE ATTIVE

L'ispezione dei socket di rete e dei processi sulla VPS rivela la seguente mappa di ascolto:

*   **Porta `8080` (TCP - Local/Tailscale):**
    *   *Servizio:* Server `llama.cpp` primario.
    *   *Modello Servito:* **NVIDIA Nemotron 3 Nano 30B-A3B** (GGUF quantizzato `UD-Q4_K_XL`).
    *   *Ruolo:* **Il Sovereign Core**. Fornisce inferenza pesante ed unificata in tempo reale sia per la logica decisionale del Trader che per i giudizi di rischio del Risk Mentor.
*   **Porta `8081` (TCP - Local/Tailscale):**
    *   *Servizio:* Server `llama.cpp` secondario.
    *   *Modello Servito:* **Llama 3.1 8B**.
    *   *Ruolo:* **Isolato ed escluso**. Non partecipa attivamente al loop di trading della V7/V8 per evitare timeout e liberare VRAM sulla doppia GPU Tesla T4.
*   **Porta `8050` (TCP - 127.0.0.1):**
    *   *Servizio:* Applicazione Web FastAPI / Uvicorn (Dashboard V6).
    *   *Path Processo:* `/broker/storage/storage-next/venv/bin/python3 -m uvicorn dashboard.main:app` (PID: `405435`).
    *   *Ruolo:* Espone la console Streamlit/FastAPI per il monitoraggio dei grafici di performance ed equity in locale.

---

## 3. PROCESSI DI TRADING ATTIVI (LE ORBITE DI PRODUZIONE)

L'audit dei processi Linux conferma che non ci sono processi orfani accumulati e che sono attive esattamente due navette di trading parallele ed indipendenti, lanciate sotto virtualenv Python isolate tramite asimmetria della variabile `$HOME`:

### 🛰️ Processo 1: Orbit A (REAL-FEE)
*   **Path Esecuzione:** `/broker/storage/storage-next/run_24h_loop.py`
*   **Interprete Python:** `/broker/storage/storage-next/venv/bin/python3`
*   **PID Attivo:** `655120`
*   **Variabili d'Ambiente Isolate:** `HOME=/broker/storage/storage-next`
*   **Database Scrittura:** `/broker/storage/storage-next/db/nemotron.sqlite`
*   **File Log Attivo:** `/broker/storage/storage-next/logs/24h_mission.log`
*   **ID Run Attiva:** `RUN-24H-FCD467`
*   **Workspace Configurato:** `fondazione-agentic-next`
*   **Regime Economico:** **Attrito Reale**. Applica una commissione fissa dello **0.26%** (Kraken Starter tier) per simulare l'impatto dei costi reali e simula uno slippage dinamico.

### 🛰️ Processo 2: Orbit B (ZERO-FEE)
*   **Path Esecuzione:** `/broker/storage/storage-zero/run_24h_loop.py`
*   **Interprete Python:** `/broker/storage/storage-zero/venv/bin/python3`
*   **PID Attivo:** `657278`
*   **Variabili d'Ambiente Isolate:** `HOME=/broker/storage/storage-zero`
*   **Database Scrittura:** `/broker/storage/storage-zero/db/nemotron.sqlite`
*   **File Log Attivo:** `/broker/storage/storage-zero/logs/24h_mission.log`
*   **ID Run Attiva:** `RUN-24H-D62687`
*   **Workspace Configurato:** `fondazione-agentic-next`
*   **Regime Economico:** **Frictionless**. Commissioni azzerate (**0.00%**) e nessuno slippage simulato. Funge da benchmark teorico puro delle performance cognitive del modello.

---

## 4. AUDIT DELLO STORAGE E PRESERVAZIONE FILE
La struttura delle directory sotto `/broker/storage` è pulita e priva di ridondanze nocive:
*   `/broker/storage/storage-next/`: Directory attiva di Orbit A. Contiene database SQLite WAL, database vettoriale LanceDB (`/vectordb/episodes.lance`) e i log di ciclo.
*   `/broker/storage/storage-zero/`: Directory attiva di Orbit B. Speculare a `storage-next` ma isolata tramite home dedicata per evitare conflitti di lock su SQLite del paper broker di Kraken.
*   `/broker/storage/storage_v5_archive/`: Archivio storico sigillato delle vecchie esecuzioni V5.0 per scopi di retro-analisi.
*   `/broker/storage/storage_v6_backup_2026-08-16.tar.gz`: Backup fisico completo dello stato del sistema prima del roll-out delle patch V7.0/V8.0.
