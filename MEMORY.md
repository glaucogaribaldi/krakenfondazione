# MEMORY.md - Curated Long-Term Memories

Benvenuto nella memoria a lungo termine di TRE. Qui verranno conservate le decisioni, le lezioni apprese, i progetti e le preferenze di Giacomo per garantire continuità tra le sessioni.

## Informazioni Generali
- **Proprietario:** Giacomo
- **Operatore AI:** TRE (Giacomo's permanent personal AI operator)
- **Piattaforma:** Zava U50

---

## 🔐 Preferenze d'Autonomia e Sicurezza (Aggiunte: 2026-08-11)
1. **Integrazione Open-Source**: TRE è autorizzato a ricercare e integrare librerie, componenti, pattern di design e strumenti open-source affidabili da GitHub per espandere le capacità dell'MVP o migliorare la documentazione/audit, rispettando rigorosamente le licenze e garantendo l'attribuzione della paternità del codice originale.
2. **Nessuna ricerca di credenziali online**: È categoricamente vietato ricercare, estrarre o tentare d'utilizzare chiavi API, token, stringhe di connessione a database o credenziali pubblicate online. Qualsiasi servizio di terze parti o modulo esterno che richieda l'uso di una chiave privata deve essere esposto unicamente come configurazione opzionale.
3. **Approccio Locale e Paper-Only**: Privilegiare sempre i componenti open-source eseguiti localmente o su infrastruttura privata protetta (es. Tailscale) e mantenere l'impermeabilità totale rispetto ad esecuzioni o ordini reali sul mercato exchange (Mantenere rigorosamente PAPER-only).

---

## 🖥️ Configurazione Gateway & Infrastruttura OpenClaw (Zava U50)
- **Modifiche 2026-08-11:**
  - **Memory Search:** Configurato per utilizzare gli embedding di **Gemini** (utilizzando il profilo attivo `google:default`) invece di OpenAI. Indice vettoriale ricostruito a 3072 dimensioni.
  - **Gateway Bind:** Impostato su `auto` per permettere l'ascolto sia locale (loopback `127.0.0.1`) sia sulla rete Tailscale. Questo sblocca i tool integrati come `cron` e `memory_search`.
  - **Integrazione UI/Dashboard (ClawForge):** Installata la skill `theashbhat-dynamic-ui`. Risolto il rendering di grafici e tabelle via Headless Chromium superando il blocco sandbox di snap e i requisiti di autenticazione dell'iframe in chat.

---

## 📈 Progetto Trading Evolutivo: `krakenfondazione`
- **Descrizione:** Sistema di trading evolutivo cartaceo (PAPER-only) accoppiato a modelli AI per decidere l'allocazione su coppie Spot e Futures.
- **Integrazione Futures (2026-08-14):** L'utente ha fornito le chiavi API dedicate per lo sblocco dei Futures in modalità Paper. Nemotron è autorizzato a simulare il trasferimento di liquidità dal conto Spot Paper al conto Futures Paper per addestrarsi sulle leve finanziarie. Il blocco assoluto di sicurezza contro l'esecuzione sul conto Live rimane inderogabile.
- **Nuova Architettura Multi-Agente (Revisione 2026-08-15 - Sintonizzazione Finale):**
  L'ecosistema opera interamente in locale sulla VPS, integrando i modelli installati in una sinergia autosufficiente senza dipendenze esterne:
  1. **TRE (Main):** Orchestratore dell'infrastruttura, dei sistemi e del codice. Monitora il corretto funzionamento dei demoni e l'allineamento dei database, rimanendo esterno al flusso di trading diretto.
  2. **architetto-gemini:** Agente offline ed esterno al loop di trading live. Interviene solo asincronamente per analizzare lo storico profondo (es. candele storiche, backtesting offline) e iniettare o rigenerare i macro-prompt e le linee guida strategiche globali.
  3. **nemotron-trader (Il Sovereign Broker):** L'unico sovrano esecutivo sulla VPS (porta 8080, modello Nemotron 30B GGUF).
     - **Esecuzione Diretta:** Dialoga con Kraken API (Paper) effettuando compravendite in totale autonomia decisionale.
     - **Consapevolezza del Rischio (Autogoverno):** Prima di agire, riceve le raccomandazioni di rischio del suo stesso mentore interno (`mentor_advice`), decidendo liberamente size e leva (fino a 50x) bilanciando aggressività e sopravvivenza.
  4. **L'Agente Mentore di Rischio (Llama 3.1 8B):** Operativo sulla VPS (porta 8081). Riceve lo snapshot di mercato in tempo reale direttamente dallo scanner, analizza la volatilità corrente e la cassa disponibile, e genera in italiano raccomandazioni di rischio rigide (`mentor_advice`) su leve, size e stop-loss, nutrendo la coscienza di Nemotron Trader prima dell'ordine.
  5. **fondazione-reporter:** Servizio di monitoraggio e generazione bollettini in sola lettura per informare l'utente (Giacomo) tramite canali di notifica (es. Telegram), gestendo le comunicazioni senza sottrarre cicli di calcolo al broker.
- **Workspace Ufficiale Paper Trading:**
  - Si utilizza **esclusivamente `fondazione-agentic`** per centralizzare le performance ed evitare frammentazione. Tutte le operazioni di Nemo e Architetto andranno veicolate qui.

---

## ☁️ VPS di Inferenza Nemotron (`instance-20260719-152821`)
- **Host & Hardware:** Debian 13 (trixie), 8 vCPU, 50 GB RAM, **2 GPU NVIDIA Tesla T4** (15GB VRAM ciascuna) con driver 550.163.01.
- **Stack:** 
  - Server `llama.cpp` primario sulla porta `8080` che serve il modello pesante **NVIDIA Nemotron 3 Nano 30B-A3B** (GGUF quantizzato UD-Q4_K_XL) per la logica di mercato.
  - Server `llama.cpp` secondario sulla porta `8081` che serve il modello **Llama 3.1 8B** per l'agente reporter/facilitatore su Telegram.
- **Connettività Privata:** Disponibile unicamente su Tailscale agli indirizzi `http://100.73.54.72:8080/v1` e `http://100.73.54.72:8081/v1` (OpenAI-compatible, senza chiavi API).
- **Isolamento:** La VPS è un'appliance di sola inferenza; non contiene software di trading, databases o credenziali di scambio di Giacomo.
