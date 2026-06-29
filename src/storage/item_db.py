import os
import sqlite3
import queue
import threading
from datetime import datetime
from typing import Dict, Any, Tuple


class ItemGuardDatabaseManager:
    """An industrial-grade, thread-safe transactional SQLite engine.
    
    Uses an internal FIFO queue and a dedicated background consumer thread
    to completely eliminate database locking exceptions during high-concurrency
    asynchronous operations.
    """

    def __init__(self, db_path: str = "data/item_bank.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._create_schema_tables()

        # Initialize the thread-safe communication queue
        self.write_queue: queue.Queue = queue.Queue()
        
        # Spin up the persistent background consumer thread
        self.worker_thread = threading.Thread(target=self._database_consumer_worker, daemon=True)
        self.worker_thread.start()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _create_schema_tables(self):
        """Builds relational structural schema tables with rigid tracking constraints."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS item_bank (
                    item_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    raw_question TEXT NOT NULL,
                    intended_key TEXT NOT NULL,
                    final_status TEXT NOT NULL,
                    total_calculated_cost REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS validation_telemetry (
                    telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    solver_status TEXT NOT NULL,
                    solver_rationale TEXT,
                    bias_score REAL NOT NULL,
                    bias_rationale TEXT,
                    generation_latency_ms INTEGER NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    FOREIGN KEY(item_id) REFERENCES item_bank(item_id)
                )
            """)
            conn.commit()

    def record_validated_item(self, item_data: Dict[str, Any], telemetry_data: Dict[str, Any]):
        """Non-blockingly drops the telemetry payload into the FIFO ingestion queue."""
        self.write_queue.put((item_data, telemetry_data))

    def _database_consumer_worker(self):
        """Dedicated background worker that safely consumes queue payloads over a single thread."""
        # Open one single persistent connection for the lifespan of this thread
        conn = self._connect()
        cursor = conn.cursor()

        while True:
            try:
                # Block until an item is pushed into the queue
                item_data, telemetry_data = self.write_queue.get()
                
                cursor.execute("""
                    INSERT INTO item_bank (item_id, timestamp, category, difficulty, raw_question, intended_key, final_status, total_calculated_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_data["item_id"],
                    datetime.utcnow().isoformat(),
                    item_data["category"],
                    item_data["difficulty"],
                    item_data["raw_question"],
                    item_data["intended_key"],
                    item_data["final_status"],
                    item_data["total_calculated_cost"]
                ))

                cursor.execute("""
                    INSERT INTO validation_telemetry (item_id, solver_status, solver_rationale, bias_score, bias_rationale, generation_latency_ms, input_tokens, output_tokens)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_data["item_id"],
                    telemetry_data["solver_status"],
                    telemetry_data["solver_rationale"],
                    telemetry_data["bias_score"],
                    telemetry_data["bias_rationale"],
                    telemetry_data["generation_latency_ms"],
                    telemetry_data["input_tokens"],
                    telemetry_data["output_tokens"]
                ))
                
                # Commit the transaction atomically
                conn.commit()
                
                # Signal the queue that the job block is completed
                self.write_queue.task_done()

            except Exception as e:
                conn.rollback()
                print(f"[Database Background Error]: Transaction rolled back: {str(e)}")