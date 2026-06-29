from typing import List, Optional
from pydantic import BaseModel, Field

class GeneratedGmatItem(BaseModel):
    """Data blueprint for an raw AI-generated psychometric question item."""
    category: str = Field(description="The test section: Quant, Verbal, or Data Insights.")
    difficulty: str = Field(description="Target item difficulty milestone: Easy, Medium, Hard.")
    question_text: str = Field(description="The core narrative text, scenario, or mathematical equation.")
    options: List[str] = Field(description="Exactly 5 multiple-choice options labeled A through E.")
    correct_key: str = Field(description="The single correct multiple-choice letter: A, B, C, D, or E.")

class SolverEvaluation(BaseModel):
    """Data blueprint for the independent adversarial verification agent."""
    calculated_steps: str = Field(description="Step-by-step logic detailing how the solver derived its answer.")
    derived_key: str = Field(description="The letter option (A-E) the solver independently arrived at.")
    keys_match: bool = Field(description="True if derived_key perfectly matches the intended correct_key.")

class BiasAuditResult(BaseModel):
    """Data blueprint for the structural demographic and linguistic auditor agent."""
    bias_detected: bool = Field(description="True if socioeconomic, regional, or demographic biases are flagged.")
    bias_score: float = Field(description="Floating point value ranging strictly from 0.0 (clean) to 1.0 (highly biased).")
    audit_rationale: str = Field(description="Detailed linguistic evaluation citing regulatory compliance benchmarks.")
    suggested_refactor: Optional[str] = Field(None, description="A completely neutralized text string if bias was detected.")