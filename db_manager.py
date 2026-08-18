import json
import sqlite3
from typing import Dict, Any, List

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # T0 and T1 records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodic_memory (
                decision_id TEXT PRIMARY KEY,
                timestamp INTEGER,
                intent_id TEXT,
                market_regime TEXT,
                market_snapshot JSON,
                strategist_view JSON,
                mentor_advice JSON,
                trader_decision JSON,
                disagreement JSON,
                action_taken JSON,
                
                -- T1 fields
                exit_timestamp INTEGER,
                outcome_pnl_pct REAL,
                outcome_mae_pct REAL,
                outcome_mfe_pct REAL,
                exit_reason TEXT,
                reflection_notes JSON
            )
        ''')

        # Beliefs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS beliefs (
                belief_id TEXT PRIMARY KEY,
                statement TEXT,
                created_by TEXT,
                supporting_trades_count INTEGER DEFAULT 0,
                contradicting_trades_count INTEGER DEFAULT 0,
                mean_return_supporting REAL DEFAULT 0.0,
                mean_return_contradicting REAL DEFAULT 0.0,
                applicable_regimes JSON,
                confidence_score REAL DEFAULT 0.0,
                status TEXT
            )
        ''')

        # Scorecards
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scorecards (
                entity_id TEXT,
                regime TEXT,
                correct_calls INTEGER DEFAULT 0,
                wrong_calls INTEGER DEFAULT 0,
                accuracy_rate REAL DEFAULT 0.0,
                avg_pnl_when_followed REAL DEFAULT 0.0,
                avg_pnl_when_ignored REAL DEFAULT 0.0,
                last_updated INTEGER,
                PRIMARY KEY (entity_id, regime)
            )
        ''')
        
        conn.commit()
        conn.close()

    def insert_t0(self, record: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO episodic_memory (
                decision_id, timestamp, intent_id, market_regime, market_snapshot, 
                strategist_view, mentor_advice, trader_decision, disagreement, action_taken
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record['decision_id'],
            record['timestamp'],
            record['intent_id'],
            record.get('market_regime', 'UNKNOWN'),
            json.dumps(record.get('market_snapshot', {})),
            json.dumps(record.get('strategist_view', {})),
            json.dumps(record.get('mentor_advice', {})),
            json.dumps(record.get('trader_decision', {})),
            json.dumps(record.get('disagreement', {})),
            json.dumps(record.get('action_taken', {}))
        ))
        conn.commit()
        conn.close()

    def update_t1(self, decision_id: str, t1_data: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE episodic_memory SET
                exit_timestamp = ?,
                outcome_pnl_pct = ?,
                outcome_mae_pct = ?,
                outcome_mfe_pct = ?,
                exit_reason = ?,
                reflection_notes = ?
            WHERE decision_id = ?
        ''', (
            t1_data['exit_timestamp'],
            t1_data['pnl_pct'],
            t1_data.get('mae_pct', 0.0),
            t1_data.get('mfe_pct', 0.0),
            t1_data.get('exit_reason', ''),
            json.dumps(t1_data.get('reflection_notes', {})),
            decision_id
        ))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    db = DatabaseManager("/tmp/test_nemotron.sqlite")
    # Test Gate 1: Insert T0
    t0_mock = {
        "decision_id": "DEC-TEST-001",
        "timestamp": 1700000000,
        "intent_id": "INT-001",
        "market_snapshot": {"price": 100},
        "action_taken": {"action": "buy", "pair": "BTCEUR"}
    }
    db.insert_t0(t0_mock)
    
    # Test Gate 2: Update T1
    t1_mock = {
        "exit_timestamp": 1700003600,
        "pnl_pct": 2.5,
        "exit_reason": "take_profit"
    }
    db.update_t1("DEC-TEST-001", t1_mock)
    print("Database Schema and T0/T1 logic successfully tested.")
