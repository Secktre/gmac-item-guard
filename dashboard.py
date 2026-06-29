import sqlite3

def run_production_metrics_dashboard():
    """Compiles enterprise analytics from the relational item bank to evaluate pipeline yield."""
    db_path = "data/item_bank.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("        SYSTEM PRODUCTION METRICS & VALIDATION REPORT DASHBOARD")
    print("="*70)

    # 1. Yield Analysis
    total_runs = cursor.execute("SELECT COUNT(*) FROM item_bank").fetchone()[0]
    approved = cursor.execute("SELECT COUNT(*) FROM item_bank WHERE final_status LIKE 'APPROVED%'").fetchone()[0]
    rejected_logic = cursor.execute("SELECT COUNT(*) FROM item_bank WHERE final_status = 'REJECTED_LOGIC'").fetchone()[0]
    rejected_bias = cursor.execute("SELECT COUNT(*) FROM item_bank WHERE final_status = 'REJECTED_BIAS'").fetchone()[0]

    yield_rate = (approved / total_runs * 100) if total_runs > 0 else 0.0

    print(f"🔹 Total Evaluated Item Assets Ingested : {total_runs}")
    print(f"   |-- APPROVED (Safe for Pool)        : {approved}")
    print(f"   |-- REJECTED_LOGIC (Failed Proof)  : {rejected_logic}")
    print(f"   |-- REJECTED_BIAS (Linguistic Drop) : {rejected_bias}")
    print(f"🔹 Total Clean Yield Efficiency Rate    : {yield_rate:.2f}%")
    print("-" * 70)

    # 2. Financial Operational Capital Metrics
    total_cost = cursor.execute("SELECT SUM(total_calculated_cost) FROM item_bank").fetchone()[0] or 0.0
    avg_latency = cursor.execute("SELECT AVG(generation_latency_ms) FROM validation_telemetry").fetchone()[0] or 0.0
    total_tokens = cursor.execute("SELECT SUM(input_tokens + output_tokens) FROM validation_telemetry").fetchone()[0] or 0

    print(f"💵 Total Consolidated LLM Financial Cost : ${total_cost:.5f}")
    print(f"📦 Total BPE Tokens Parsed (cl100k_base): {total_tokens:,} tokens")
    print(f"⚡ Average Asynchronous Node Latency     : {avg_latency/1000:.2f} seconds")
    print("-" * 70)

    # 3. Micro-Audit Log Trace
    print("📋 RECENT PIPELINE TRANSACTION LOG (LAST 5 ITERATIONS):")
    query = """
        SELECT i.item_id, i.category, i.difficulty, i.final_status, t.solver_status, t.bias_score 
        FROM item_bank i 
        JOIN validation_telemetry t ON i.item_id = t.item_id 
        ORDER BY i.timestamp DESC LIMIT 5
    """
    for row in cursor.execute(query).fetchall():
        print(f"  Item [{row[0]}] | {row[1]:<13} | {row[2]:<6} | Status: {row[3]:<19} | Solver: {row[4]:<8} | Bias Score: {row[5]:.2f}")

    print("="*70 + "\n")
    conn.close()

if __name__ == "__main__":
    run_production_metrics_dashboard()