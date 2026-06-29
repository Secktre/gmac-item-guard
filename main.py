import asyncio
import time
import logging
from typing import Dict, Any, List
from src.storage.item_db import ItemGuardDatabaseManager
from src.engine.nodes import PsychometricItemGuardEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BatchFactory")

INPUT_TOKEN_RATE = 0.0015
OUTPUT_TOKEN_RATE = 0.0020

def calculate_exact_cost(input_tokens: int, output_tokens: int) -> float:
    in_cost = (input_tokens / 1000) * INPUT_TOKEN_RATE
    out_cost = (output_tokens / 1000) * OUTPUT_TOKEN_RATE
    return round(in_cost + out_cost, 6)

async def orchestrate_single_job(engine: PsychometricItemGuardEngine, db: ItemGuardDatabaseManager, job_params: Dict[str, str]):
    category = job_params["category"]
    difficulty = job_params["difficulty"]
    
    logger.info(f"Worker initiated for job target: {category} ({difficulty})")
    telemetry = await engine.process_pipeline_item_async(category, difficulty)
    total_cost = calculate_exact_cost(telemetry["input_tokens"], telemetry["output_tokens"])
    
    item_record = {
        "item_id": telemetry["item_id"],
        "category": telemetry["category"],
        "difficulty": telemetry["difficulty"],
        "raw_question": telemetry["raw_question"],
        "intended_key": telemetry["intended_key"],
        "final_status": telemetry["final_status"],
        "total_calculated_cost": total_cost
    }

    telemetry_record = {
        "solver_status": telemetry["solver_status"],
        "solver_rationale": telemetry["solver_rationale"],
        "bias_score": telemetry["bias_score"],
        "bias_rationale": telemetry["bias_rationale"],
        "generation_latency_ms": telemetry["latency_ms"],
        "input_tokens": telemetry["input_tokens"],
        "output_tokens": telemetry["output_tokens"]
    }

    # Drops data into queue non-blockingly instantly
    db.record_validated_item(item_record, telemetry_record)
    logger.info(f"Worker finished processing pipeline nodes for: {telemetry['item_id']} [Pushed to Write Queue]")

async def main():
    start_time = time.time()
    
    db = ItemGuardDatabaseManager()
    engine = PsychometricItemGuardEngine(generation_model="llama3", evaluation_model="llama3")

    job_queue: List[Dict[str, str]] = [
        {"category": "Quant", "difficulty": "Hard"},
        {"category": "Verbal", "difficulty": "Medium"},
        {"category": "Data Insights", "difficulty": "Hard"},
        {"category": "Verbal", "difficulty": "Hard"}
    ]

    logger.info(f"======================================================================")
    logger.info(f"INITIALIZING ASYNC BATCH FACTORY RUNTIME | PIPELINE QUEUE: {len(job_queue)}")
    logger.info(f"======================================================================")

    tasks = [orchestrate_single_job(engine, db, job) for job in job_queue]
    await asyncio.gather(*tasks)

    # CRITICAL PRODUCTION BLOCK: Block main thread exit until background database queue is completely empty
    logger.info("Awaiting background database worker queue synchronization...")
    db.write_queue.join()

    total_latency = round(time.time() - start_time, 2)
    logger.info(f"======================================================================")
    logger.info(f"BATCH OPERATIONS COMPLETE | TOTAL PROCESSING LATENCY: {total_latency}s")
    logger.info(f"======================================================================")

if __name__ == "__main__":
    asyncio.run(main())