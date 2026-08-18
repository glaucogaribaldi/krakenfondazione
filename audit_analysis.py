import requests
import json
import os

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"
LLAMA_URL = "http://100.73.54.72:8081/v1/chat/completions"

# 1. Recupero dati reali
balance_data = {
    "current_value_eur": 293.04,
    "starting_balance": 297.68,
    "total_trades": 38,
    "unrealized_pnl_pct": -1.55,
    "holdings": {"EUR": 0.79, "SOL": 4.47}
}

training_data = "22.000 steps completati in 50 ambienti RL in parallelo negli ultimi 220 minuti."

# 2. Interrogo Architetto-Gemini (simulato tramite chiamata locale)
# OpenClaw non ha un endpoint locale diretto per "architetto-gemini", lo gestisce l'orchestratore. 
# Creerò un prompt da fare processare a Gemini 3.5 per fargli fare la parte dell'Architetto.
print("--- Preparazione Audit ---")
