import sqlite3
import os
import shutil
import sys
import uuid

def migrate_db_to_v2(db_path="/broker/storage/storage-next/db/nemotron.sqlite"):
    """
    Idempotent database migration script from V1.0 schema to V2.0 transactional schema.
    Performs safety copy, detects current columns, creates temporary table,
    migrates data with generated UUIDs, renames tables within a transaction,
    and sets PRAGMA user_version to 2.
    """
    print(f"Starting database migration to V2.0 for: {db_path}")
    if not os.path.exists(db_path):
        print(f"No database found at {db_path} to migrate. Initializing fresh schema.")
        from nemoforge.db_init_v2 import init_db_v2
        init_db_v2(db_path)
        return True
        
    # 1. Execute safety backup before any migration operations
    backup_path = db_path + ".backup_migration"
    print(f"Creating safety backup at {backup_path}...")
    shutil.copy2(db_path, backup_path)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Check current user_version
        c.execute("PRAGMA user_version")
        version = c.fetchone()[0]
        if version >= 2:
            print(f"Database is already at schema version {version}. No migration needed.")
            conn.close()
            return True
            
        # Detect if paper_positions has 'position_id' as primary key
        c.execute("PRAGMA table_info(paper_positions)")
        columns = c.fetchall()
        column_names = [col[1] for col in columns]
        pk_cols = [col[1] for col in columns if col[5] == 1] # col[5] is primary key flag
        
        needs_migration = False
        if "position_id" not in column_names or "symbol" in pk_cols:
            needs_migration = True
            
        if needs_migration:
            print("Migration required for 'paper_positions' table. Starting SQL transaction...")
            
            # Start transaction explicitly
            c.execute("BEGIN TRANSACTION")
            
            # 1. Create temporary v2 table
            c.execute('''
                CREATE TABLE IF NOT EXISTS paper_positions_v2 (
                    position_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    symbol TEXT,
                    side TEXT,
                    size REAL,
                    average_entry_price REAL,
                    leverage REAL,
                    cumulative_fees REAL,
                    accumulated_funding REAL,
                    tp_price REAL,
                    sl_price REAL,
                    opened_at INTEGER,
                    last_updated INTEGER,
                    status TEXT
                )
            ''')
            
            # 2. Extract existing V1 rows
            # V1 columns: symbol (PK), run_id, side, size, average_entry_price, leverage, cumulative_fees, accumulated_funding, tp_price, sl_price, opened_at, last_updated, status
            # Find matching columns in old table
            old_cols_str = ", ".join([col for col in column_names if col != "position_id"])
            c.execute(f"SELECT {old_cols_str} FROM paper_positions")
            old_rows = c.fetchall()
            
            print(f"Migrating {len(old_rows)} existing rows from old table...")
            for row in old_rows:
                # Generate unique position_id
                pos_id = f"POS-{uuid.uuid4().hex[:6].upper()}"
                
                # Reconstruct full row mapping based on columns
                row_dict = dict(zip([col for col in column_names if col != "position_id"], row))
                
                # Insert into v2 table
                c.execute('''
                    INSERT INTO paper_positions_v2 (
                        position_id, run_id, symbol, side, size, average_entry_price, 
                        leverage, cumulative_fees, accumulated_funding, tp_price, sl_price, 
                        opened_at, last_updated, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pos_id,
                    row_dict.get("run_id", "RUN-MIGRATED"),
                    row_dict.get("symbol"),
                    row_dict.get("side", "short"),
                    row_dict.get("size", 0.0),
                    row_dict.get("average_entry_price", 0.0),
                    row_dict.get("leverage", 10.0),
                    row_dict.get("cumulative_fees", 0.0),
                    row_dict.get("accumulated_funding", 0.0),
                    row_dict.get("tp_price", 0.0),
                    row_dict.get("sl_price", 0.0),
                    row_dict.get("opened_at", int(time.time())),
                    row_dict.get("last_updated", int(time.time())),
                    row_dict.get("status", "CLOSED")
                ))
            
            # 3. Drop old table and rename new table
            c.execute("DROP TABLE paper_positions")
            c.execute("ALTER TABLE paper_positions_v2 RENAME TO paper_positions")
            
            # 4. Create partial unique index
            c.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_active_pos 
                ON paper_positions(run_id, symbol) 
                WHERE status = 'OPEN'
            ''')
            
            # 5. Set user_version to 2
            c.execute("PRAGMA user_version = 2")
            
            # Commit transaction
            conn.commit()
            print("SUCCESS: Database migration transaction committed successfully!")
        else:
            print("No migration required for 'paper_positions'. Database is already up-to-date.")
            
        conn.close()
        return True
    except Exception as e:
        print(f"CRITICAL ERROR during database migration: {e}. Executing rollback...")
        conn.rollback()
        conn.close()
        # Restore backup in case of catastrophic failure
        shutil.copy2(backup_path, db_path)
        print("Rollback completed. Original database restored from backup.")
        return False

if __name__ == '__main__':
    db = "/broker/storage/storage-next/db/nemotron.sqlite" if len(sys.argv) < 2 else sys.argv[1]
    migrate_db_to_v2(db)
