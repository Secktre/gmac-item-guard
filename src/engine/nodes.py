import time
import uuid
import re
import asyncio
import logging
import tiktoken
from typing import Dict, Any, List
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from .schemas import GeneratedGmatItem, SolverEvaluation, BiasAuditResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ItemGuardEngine")

class RegulatoryComplianceViolation(Exception):
    """Raised when an item explicitly violates foundational psychometric standardization boundaries."""
    pass

class PsychometricItemGuardEngine:
    """An enterprise-grade asynchronous validation engine executing multi-stage psychometric item auditing.
    
    Implements a self-healing critique loop to autonomously repair logically flawed question
    generations before committing to the transactional data ledger.
    """
    
    def __init__(self, generation_model: str = "llama3", evaluation_model: str = "llama3"):
        self.gen_model_name = generation_model
        self.eval_model_name = evaluation_model
        
        self.unconstrained_llm = ChatOllama(model=evaluation_model, temperature=0.0)
        self.generator_client = ChatOllama(model=generation_model, temperature=0.7).with_structured_output(GeneratedGmatItem)
        self.solver_extractor = self.unconstrained_llm.with_structured_output(SolverEvaluation)
        self.auditor_extractor = self.unconstrained_llm.with_structured_output(BiasAuditResult)
        
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.forbidden_idioms = [
            r"\bwall street\b", r"\b401k\b", r"\bcricket match\b", 
            r"\bbaseball\b", r"\bsuper bowl\b", r"\bivy league\b"
        ]

    def _calculate_exact_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self.tokenizer.encode(text))

    def _deterministic_bias_scan(self, text: str) -> List[str]:
        return [pattern for pattern in self.forbidden_idioms if re.search(pattern, text.lower())]

    async def _execute_with_retry(self, chain, input_data: dict, retries: int = 3, initial_delay: float = 1.0):
        delay = initial_delay
        for attempt in range(retries):
            try:
                return await chain.ainvoke(input_data)
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                logger.warning(f"Transient model error on attempt {attempt + 1}. Retrying in {delay}s... Details: {e}")
                await asyncio.sleep(delay)
                delay *= 2

    async def process_pipeline_item_async(self, category: str, difficulty: str) -> Dict[str, Any]:
        """Asynchronously orchestrates multi-stage item generation, verification, and automated refactoring."""
        item_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        telemetry = {
            "item_id": item_id, "category": category, "difficulty": difficulty,
            "raw_question": "", "intended_key": "", "solver_status": "PENDING",
            "solver_rationale": "", "bias_score": 0.0, "bias_rationale": "",
            "final_status": "FAILED_SYSTEM", "latency_ms": 0, "input_tokens": 0, "output_tokens": 0
        }

        try:
            # Stage 1: Initial Item Generation
            gen_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an elite psychometric system. Create a complex GMAT multiple-choice question. Return JSON."),
                ("user", "Generate a unique '{difficulty}' level '{category}' item with 5 plausible options.")
            ])
            telemetry["input_tokens"] += self._calculate_exact_tokens(str(gen_prompt))
            gen_chain = gen_prompt | self.generator_client
            result: GeneratedGmatItem = await self._execute_with_retry(gen_chain, {"category": category, "difficulty": difficulty})
            
            # Master control flags for the self-healing engine loop
            passes_logic = False
            max_remediation_attempts = 2
            attempt_count = 0
            
            while not passes_logic and attempt_count < max_remediation_attempts:
                attempt_count += 1
                
                # Update tracking payloads for this specific attempt iteration
                full_item_text = f"{result.question_text} Options: {', '.join(result.options)}"
                telemetry["raw_question"] = full_item_text
                telemetry["intended_key"] = result.correct_key
                telemetry["output_tokens"] += self._calculate_exact_tokens(str(result.model_dump()))

                # Stage 2: Static Compliance Pass
                static_violations = self._deterministic_bias_scan(result.question_text)
                if static_violations:
                    raise RegulatoryComplianceViolation(f"Static compliance dictionary match detected: {static_violations}")

                # Stage 3: Unconstrained Blind Adversarial Verification
                solve_prompt = ChatPromptTemplate.from_messages([
                    ("system", (
                        "You are an independent, adversarial psychometric grading kernel. "
                        "Isolate the question text from its metadata, process the prompt scenario step-by-step from scratch, "
                        "and write out an absolute logical explanation proving which option is uniquely correct. "
                        "Conclude your execution by stating exactly: 'The correct answer choice is: [Insert Option Letter]'."
                    )),
                    ("user", "Question: {question}\nOptions: {options}")
                ])
                telemetry["input_tokens"] += self._calculate_exact_tokens(str(solve_prompt))
                
                raw_reasoning_response = await self._execute_with_retry(
                    (solve_prompt | self.unconstrained_llm), 
                    {"question": result.question_text, "options": ", ".join(result.options)}
                )
                raw_reasoning_text = raw_reasoning_response.content
                telemetry["output_tokens"] += self._calculate_exact_tokens(raw_reasoning_text)

                # Stage 4: Structure Extraction Pass for Solver Metadata
                extraction_prompt = ChatPromptTemplate.from_messages([
                    ("system", "Read the following technical proof and extract the data into structured format matching the JSON schema."),
                    ("user", "Proof Text:\n{proof}\nExtract the derived answer key and verify if it matches intended key: '{intended_key}'.")
                ])
                telemetry["input_tokens"] += self._calculate_exact_tokens(str(extraction_prompt))
                extract_chain = extraction_prompt | self.solver_extractor
                
                solver_res: SolverEvaluation = await self._execute_with_retry(extract_chain, {
                    "proof": raw_reasoning_text,
                    "intended_key": result.correct_key
                })
                
                passes_logic = solver_res.derived_key.strip().upper() == result.correct_key.strip().upper()
                telemetry["solver_status"] = "MATCH" if passes_logic else "MISMATCH"
                telemetry["solver_rationale"] = raw_reasoning_text
                
                if not passes_logic:
                    if attempt_count >= max_remediation_attempts:
                        logger.warning(f"Item {item_id} exhausted all remediation attempts without solving successfully. Rejecting logic completely.")
                        telemetry["final_status"] = "REJECTED_LOGIC"
                        return telemetry
                    
                    logger.info(f"Item {item_id} failed blind logic gate on attempt {attempt_count}. Initializing Critique & Refactor Loop...")
                    
                    # CRITICAL SELF-HEALING BLOCK: Feed the failure critique back to the generator model
                    remediation_prompt = ChatPromptTemplate.from_messages([
                        ("system", "You are an elite psychometric engineer. Your previous question output contained a structural logic flaw or incorrect answer key designation. Analyze the checker's proof and rewrite the entire question, options, and answer key to make it completely flawless. Return valid JSON matching the schema."),
                        ("user", "Broken Question: {broken_question}\nYour Declared Key: {broken_key}\nChecker's Proof & Correction: {critique}")
                    ])
                    telemetry["input_tokens"] += self._calculate_exact_tokens(str(remediation_prompt))
                    
                    result = await self._execute_with_retry(
                        (remediation_prompt | self.generator_client),
                        {
                            "broken_question": result.question_text,
                            "broken_key": result.correct_key,
                            "critique": raw_reasoning_text
                        }
                    )
                    continue

            # Stage 5: Unconstrained Linguistic Compliance Pass (Only hits if logic is completely cured)
            audit_prompt = ChatPromptTemplate.from_messages([
                ("system", "Audit this text string for international socioeconomic equity. Write a detailed analysis of any cultural idioms or regional bias found."),
                ("user", "Analyze: '{text}'")
            ])
            telemetry["input_tokens"] += self._calculate_exact_tokens(str(audit_prompt))
            
            raw_audit_response = await self._execute_with_retry((audit_prompt | self.unconstrained_llm), {"text": result.question_text})
            raw_audit_text = raw_audit_response.content
            telemetry["output_tokens"] += self._calculate_exact_tokens(raw_audit_text)

            # Stage 6: Structure Extraction Pass for Auditor Metadata
            audit_extract_prompt = ChatPromptTemplate.from_messages([
                ("system", "Read the linguistic audit report and extract metadata parameters matching the JSON schema."),
                ("user", "Audit Report:\n{report}")
            ])
            telemetry["input_tokens"] += self._calculate_exact_tokens(str(audit_extract_prompt))
            audit_extract_chain = audit_extract_prompt | self.auditor_extractor
            
            audit_res: BiasAuditResult = await self._execute_with_retry(audit_extract_chain, {"report": raw_audit_text})
            telemetry["bias_score"] = audit_res.bias_score
            telemetry["bias_rationale"] = raw_audit_text
            
            if audit_res.bias_detected or audit_res.bias_score > 0.4:
                telemetry["final_status"] = "REJECTED_BIAS"
            else:
                telemetry["final_status"] = f"APPROVED_REMEDIATED" if attempt_count > 1 else "APPROVED"

        except RegulatoryComplianceViolation as rcv:
            telemetry["final_status"] = "REJECTED_STATIC_BIAS"
            telemetry["bias_rationale"] = str(rcv)
            telemetry["bias_score"] = 1.0
            logger.warning(f"Item {item_id} rejected via static compliance filter.")
        except Exception as e:
            telemetry["final_status"] = "FAILED_SYSTEM"
            telemetry["solver_rationale"] = f"Pipeline Crash Exception: {str(e)}"
            logger.error(f"Critical execution exception encountered for item {item_id}: {e}")
        finally:
            telemetry["latency_ms"] = int((time.time() - start_time) * 1000)
            
        return telemetry