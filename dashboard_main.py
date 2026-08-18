import os
import json
import sqlite3
import time
import subprocess
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Nemotron Sovereign Terminal API")

DB_PATH = "/broker/storage/storage-next/db/nemotron.sqlite"
LOG_PATH = "/broker/storage/storage-next/logs/24h_mission.log"
POCKETS_PATH = "/broker/storage/storage-next/db/pockets.json"
GUARDRAILS_PATH = "/broker/storage/storage-next/db/dynamic_guardrails.txt"
KRAKEN_PATH = "/home/tre/.local/bin/kraken"

# Setup templates directory
templates = Jinja2Templates(directory="/broker/storage/storage-next/dashboard/templates")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/status")
async def get_status():
    try:
        conn = get_db_connection()
        run = conn.execute("SELECT run_id, start_time, end_time, initial_equity_eur, target_equity_eur, status FROM runs WHERE status = 'ACTIVE' LIMIT 1").fetchone()
        
        # Carica i pockets aggiornati
        spot_pocket = 0.0
        futures_pocket = 0.0
        if os.path.exists(POCKETS_PATH):
            with open(POCKETS_PATH) as f:
                data = json.load(f)
                spot_pocket = float(data.get("spot_pocket", 0.0))
                futures_pocket = float(data.get("futures_pocket", 0.0))
                
        # Carica i guardrails dinamici (Pilastro 2)
        guardrails = ""
        if os.path.exists(GUARDRAILS_PATH):
            with open(GUARDRAILS_PATH) as f:
                guardrails = f.read().strip()
                
        # Estrai le posizioni attive direttamente dalla CLI di kraken
        positions = []
        try:
            # V6.3: Rimuoviamo KRAKEN_WORKSPACE per evitare il bug di validazione
            env = os.environ.copy()
            env.pop("KRAKEN_WORKSPACE", None)
            res = subprocess.run(f"env -u KRAKEN_WORKSPACE {KRAKEN_PATH} futures paper positions -o json", shell=True, capture_output=True, text=True, env=env)
            if res.returncode == 0 and res.stdout.strip():
                positions_data = json.loads(res.stdout)
                positions = positions_data.get("positions", [])
        except Exception as pe:
            logging.error(f"Error fetching paper positions: {pe}")
            
        # Estrai l'affidabilità del mentore (Pilastro 3)
        mentor_reliability = 0.8
        try:
            row = conn.execute("SELECT accuracy_rate FROM scorecards WHERE entity_id = 'mentor' LIMIT 1").fetchone()
            if row and row["accuracy_rate"] is not None:
                mentor_reliability = float(row["accuracy_rate"])
        except Exception:
            pass
            
        # Estrai la memoria episodica recente (Pilastro 1)
        recent_trades = []
        try:
            rows = conn.execute("""
                SELECT timestamp, action_taken, outcome_pnl_pct, exit_reason 
                FROM episodic_memory 
                WHERE exit_reason IS NOT NULL AND exit_reason != ''
                ORDER BY timestamp DESC LIMIT 5
            """).fetchall()
            for r in rows:
                act = json.loads(r["action_taken"])
                recent_trades.append({
                    "timestamp": r["timestamp"],
                    "pair": act.get("pair"),
                    "action": act.get("action"),
                    "leverage": act.get("leverage"),
                    "pnl": r["outcome_pnl_pct"],
                    "reason": r["exit_reason"]
                })
        except Exception:
            pass
            
        conn.close()
        
        # Calcolo dell'equity unificata reale
        current_equity = spot_pocket + futures_pocket
        
        uptime = 0
        run_data = None
        if run:
            uptime = int(time.time()) - run["start_time"]
            run_data = {
                "run_id": run["run_id"],
                "start_time": run["start_time"],
                "end_time": run["end_time"],
                "initial_equity_eur": run["initial_equity_eur"],
                "target_equity_eur": run["target_equity_eur"],
                "status": run["status"]
            }
            
        return JSONResponse(content={
            "run": run_data,
            "uptime_seconds": uptime,
            "equity": {
                "spot_pocket": spot_pocket,
                "futures_pocket": futures_pocket,
                "unified_equity": round(current_equity, 2),
                "pnl_pct": round(((current_equity - run["initial_equity_eur"]) / run["initial_equity_eur"] * 100), 2) if run else 0.0
            },
            "guardrails": guardrails,
            "mentor_reliability": mentor_reliability,
            "positions": positions,
            "recent_trades": recent_trades
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/logs")
async def get_logs(lines: int = 40):
    try:
        if not os.path.exists(LOG_PATH):
            return JSONResponse(content={"logs": "Nessun log registrato."})
            
        # Legge le ultime righe del file dei log
        cmd = f"tail -n {lines} {LOG_PATH}"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return JSONResponse(content={"logs": res.stdout.strip()})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/control/flat")
async def force_flat():
    try:
        # Avvia in background la procedura di flattening della run attiva sulla VPS
        cmd = f"KRAKEN_WORKSPACE=fondazione-agentic-next /broker/storage/storage-next/venv/bin/python3 -c 'import sys; sys.path.append(\"/broker/storage/storage-next\"); from run_24h_loop import flatten_portfolio; flatten_portfolio()'"
        subprocess.Popen(cmd, shell=True)
        return JSONResponse(content={"ok": True, "message": "Piazzato comando d'emergenza FLATTENING in background."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/control/new_run")
async def start_new_run(request: Request):
    try:
        body = await request.json()
        target_val = float(body.get("target_eur", 500.0))
        
        # 1. Fermiamo qualsiasi loop di trading attivo
        subprocess.run("pkill -9 -f run_24h_loop", shell=True)
        
        # 2. Inizializziamo il bootstrap
        bootstrap_cmd = "/broker/storage/storage-next/venv/bin/python3 /broker/storage/storage-next/bootstrap_24h.py"
        res = subprocess.run(bootstrap_cmd, shell=True, capture_output=True, text=True)
        
        # 3. Aggiorniamo SQLite per impostare l'esatto target personalizzato richiesto da Giacomo
        update_cmd = f"python3 -c \"import sqlite3; conn=sqlite3.connect('{DB_PATH}'); conn.execute('UPDATE runs SET target_equity_eur = {target_val} WHERE status = \\'ACTIVE\\\''); conn.commit(); conn.close()\""
        subprocess.run(update_cmd, shell=True)
        
        # 4. Facciamo ripartire il loop di trading in background con la V6.3
        loop_cmd = "nohup /broker/storage/storage-next/venv/bin/python3 /broker/storage/storage-next/run_24h_loop.py > /broker/storage/storage-next/logs/nohup_loop.out 2>&1 &"
        subprocess.Popen(loop_cmd, shell=True)
        
        return JSONResponse(content={"ok": True, "message": f"Avviata con successo nuova run di 24 ore con Target a €{target_val:.2f}."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8050)
