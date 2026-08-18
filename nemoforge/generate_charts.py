import json
import datetime
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

# Set dark background and custom styling
plt.style.use('dark_background')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10
plt.rcParams['grid.color'] = '#1e1e1e'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.linewidth'] = 0.5

# Hex Colors
COLOR_ZERO_FEE = '#26a69a'  # Teal/Green
COLOR_REAL_FEE = '#ef5350'  # Coral Red
COLOR_BACKGROUND = '#0c0d12'  # Deep Slate Dark
COLOR_CARD = '#151720'
COLOR_TEXT_MUTED = '#8a90a6'

# Dynamic path resolution depending on where it's executed (VPS vs U50)
BASE_PATH = "/broker/storage/storage-next" if os.path.exists("/broker/storage/storage-next") else "./"
DB_PATH = os.path.join(BASE_PATH, "db/nemotron.sqlite")
POCKETS_NEXT_PATH = os.path.join(BASE_PATH, "db/pockets.json")
LOG_PATH = os.path.join(BASE_PATH, "logs/24h_mission.log")
CHARTS_DIR = os.path.join(BASE_PATH, "charts")

def load_data():
    # Load metadata dynamically on the VPS or fallback
    import sqlite3
    start_ts = 1787063588
    initial_equity_usd = 344.84
    run_id = "RUN-24H-B42F1A"
    
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT start_time, initial_equity_eur, run_id FROM runs WHERE status = 'ACTIVE' LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                start_ts = row[0]
                initial_equity_usd = row[1] * 1.1584  # Convert initial EUR back to USD
                run_id = row[2]
        except Exception as e:
            print(f"Error querying active run DB: {e}")
            
    # Load current actual Next USD equity
    current_next_usd = 344.84
    try:
        import subprocess
        KRAKEN_PATH = "/home/tre/.local/bin/kraken"
        cmd = f"env -u KRAKEN_WORKSPACE HOME={BASE_PATH} {KRAKEN_PATH} futures paper status -o json"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        data = json.loads(res.stdout)
        current_next_usd = float(data.get('equity', 344.84))
    except Exception as e:
        print(f"Error fetching real-time futures status: {e}")

    # Parse logs directly on the VPS
    next_series = []
    if os.path.exists(LOG_PATH):
        import re
        with open(LOG_PATH, 'r') as f:
            for line in f:
                if 'Current Unified Equity:' in line:
                    m_time = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    m_eq = re.search(r'Current Unified Equity: \D*([\d.]+)', line)
                    if m_time and m_eq:
                        dt_utc = datetime.datetime.strptime(m_time.group(1), '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
                        ts = dt_utc.timestamp()
                        if ts >= start_ts:
                            next_series.append({'timestamp': dt_utc, 'equity': float(m_eq.group(1))})
                            
    df_next = pd.DataFrame(next_series)
    if df_next.empty:
        # Fallback if no log points recorded yet
        start_dt = datetime.datetime.fromtimestamp(start_ts, tz=datetime.timezone.utc)
        df_next = pd.DataFrame([{'timestamp': start_dt, 'equity': initial_equity_usd / 1.1584}])
        
    df_next = df_next.sort_values('timestamp').drop_duplicates('timestamp')
    df_next.set_index('timestamp', inplace=True)
    df = df_next.ffill().dropna()
    
    # Append the latest real-time data point converted to EUR
    last_ts = datetime.datetime.now(datetime.timezone.utc)
    df.loc[last_ts] = [current_next_usd / 1.1584]
    
    # Scale to EUR equivalent
    df['scaled_next'] = df['equity']
    df['peak_next'] = df['scaled_next'].cummax()
    df['dd_next'] = (df['scaled_next'] - df['peak_next']) / df['peak_next'] * 100
    df['perf_next'] = (df['scaled_next'] / 297.68 - 1.0) * 100
    df['cost_impact'] = 297.68 - df['scaled_next']
    
    return df, 297.68, run_id

def generate_equity_curve(df, initial_equity, run_id, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=COLOR_BACKGROUND)
    ax.set_facecolor(COLOR_BACKGROUND)
    
    ax.plot(df.index, df['scaled_next'], color=COLOR_REAL_FEE, linewidth=2, label=f'Run {run_id} (Real-Fee)')
    ax.axhline(initial_equity, color=COLOR_TEXT_MUTED, linestyle=':', alpha=0.5, label=f'Capitale Iniziale (€{initial_equity:.2f})')
    
    ax.set_title(f'EQUITY CURVE — {run_id}', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Valore Portafoglio (EUR)', fontsize=11, color=COLOR_TEXT_MUTED)
    ax.legend(loc='upper left', frameon=True, facecolor=COLOR_CARD, edgecolor='#1e1e1e')
    ax.grid(True)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.tick_params(colors=COLOR_TEXT_MUTED)
    
    text_box = (
        f"Run ID: {run_id}\n"
        f"Equity Attuale: €{df['scaled_next'].iloc[-1]:.2f}\n"
        f"Rendimento: {df['perf_next'].iloc[-1]:+.4f}%\n"
        f"Capitale Iniziale: €{initial_equity:.2f}"
    )
    ax.text(0.02, 0.05, text_box, transform=ax.transAxes, fontsize=9,
            verticalalignment='bottom', bbox=dict(boxstyle='round,pad=0.5', facecolor=COLOR_CARD, edgecolor='#1e1e1e', alpha=0.8))
            
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'equity_curve_1640.png'), dpi=150, facecolor=COLOR_BACKGROUND)
    plt.close(fig)

def generate_drawdown(df, run_id, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=COLOR_BACKGROUND)
    ax.set_facecolor(COLOR_BACKGROUND)
    
    ax.fill_between(df.index, df['dd_next'], 0, color=COLOR_REAL_FEE, alpha=0.2, step='post', label=f'Run {run_id} Drawdown')
    ax.plot(df.index, df['dd_next'], color=COLOR_REAL_FEE, linewidth=1.5, drawstyle='steps-post')
    
    ax.set_title(f'DRAWDOWN PROFILE — {run_id}', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Drawdown %', fontsize=11, color=COLOR_TEXT_MUTED)
    ax.legend(loc='lower left', frameon=True, facecolor=COLOR_CARD, edgecolor='#1e1e1e')
    ax.grid(True)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.tick_params(colors=COLOR_TEXT_MUTED)
    
    max_dd_next = df['dd_next'].min()
    text_box = f"Max DD: {max_dd_next:.4f}%"
    ax.text(0.02, 0.95, text_box, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor=COLOR_CARD, edgecolor='#1e1e1e', alpha=0.8))
            
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'drawdown_1640.png'), dpi=150, facecolor=COLOR_BACKGROUND)
    plt.close(fig)

def generate_cost_impact(df, initial_equity, run_id, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=COLOR_BACKGROUND)
    ax.set_facecolor(COLOR_BACKGROUND)
    
    cost_drag = df['cost_impact']
    ax.plot(df.index, cost_drag, color='#ffb74d', linewidth=2, label='Costi Cumulati (Fee + Slip)')
    
    ax.set_title(f'COST DRAG IMPACT — {run_id}', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Costi Cumulati (EUR)', fontsize=11, color=COLOR_TEXT_MUTED)
    ax.legend(loc='upper left', frameon=True, facecolor=COLOR_CARD, edgecolor='#1e1e1e')
    ax.grid(True)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.tick_params(colors=COLOR_TEXT_MUTED)
    
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'cost_impact_1640.png'), dpi=150, facecolor=COLOR_BACKGROUND)
    plt.close(fig)

def generate_performance(df, run_id, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=COLOR_BACKGROUND)
    ax.set_facecolor(COLOR_BACKGROUND)
    
    ax.plot(df.index, df['perf_next'], color=COLOR_REAL_FEE, linewidth=2, label='Performance %')
    ax.axhline(0, color='#ffffff', linestyle='-', alpha=0.3)
    
    ax.set_title(f'PERFORMANCE % — {run_id}', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Performance %', fontsize=11, color=COLOR_TEXT_MUTED)
    ax.legend(loc='upper left', frameon=True, facecolor=COLOR_CARD, edgecolor='#1e1e1e')
    ax.grid(True)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.tick_params(colors=COLOR_TEXT_MUTED)
    
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'performance_1640.png'), dpi=150, facecolor=COLOR_BACKGROUND)
    plt.close(fig)

if __name__ == '__main__':
    os.makedirs(CHARTS_DIR, exist_ok=True)
    
    df, initial_equity, run_id = load_data()
    generate_equity_curve(df, initial_equity, run_id, CHARTS_DIR)
    generate_drawdown(df, run_id, CHARTS_DIR)
    generate_cost_impact(df, initial_equity, run_id, CHARTS_DIR)
    generate_performance(df, run_id, CHARTS_DIR)
    print(f"SUCCESS: 4 unscaled charts generated directly on VPS/Local in: {CHARTS_DIR}")
