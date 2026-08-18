import lancedb
import pyarrow as pa
import pandas as pd
from db_manager import DatabaseManager
import uuid

class MemoryVectorDB:
    def __init__(self, uri="/broker/storage/vectordb"):
        self.db = lancedb.connect(uri)
        # We need an embedding function. Since we don't have one loaded, 
        # we can use a mock embedding or just schema for now.
        # But wait, we need actual embeddings.
        # We can use the local default embedding or just skip semantic for the MVP.
        # Let's define the schema without embeddings for now, just to have the structure.
        schema = pa.schema([
            pa.field("decision_id", pa.string()),
            pa.field("rationale", pa.string()),
            pa.field("pnl_pct", pa.float32())
        ])
        if "episodes" not in self.db.table_names():
            self.tbl = self.db.create_table("episodes", schema=schema)
        else:
            self.tbl = self.db.open_table("episodes")

    def insert_episode(self, decision_id, rationale, pnl_pct):
        df = pd.DataFrame([{"decision_id": decision_id, "rationale": rationale, "pnl_pct": pnl_pct}])
        self.tbl.add(df)

if __name__ == "__main__":
    vdb = MemoryVectorDB()
    vdb.insert_episode(f"DEC-{uuid.uuid4().hex[:8]}", "Bought ETH on volume spike", 2.5)
    print("LanceDB Episodic Vector Table initialized and populated.")
