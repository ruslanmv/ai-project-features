"""AI agents for Aurora multi-phase refactoring pipeline.

This package contains specialized agents for each phase of the refactoring
workflow. Each agent implements a specific responsibility following the
Single Responsibility Principle.

Agents:
    - RequestParserAgent (P1): Extracts constraints from user prompts
    - ArchitectureLookupAgent (P2): Analyzes codebase architecture
    - TaskPlannerAgent (P3): Decomposes work into actionable tasks
    - FeatureDesignerAgent (P4): Designs feature implementation
    - CodeGeneratorAgent (P5): Generates code patches
    - StaticCheckerAgent (D1): Validates generated code
    - DocAssemblerAgent (P6): Creates final documentation recap
"""

__all__ = [
    "BaseAgent",
    "RequestParserAgent",
    "ArchitectureLookupAgent",
    "TaskPlannerAgent",
    "FeatureDesignerAgent",
    "CodeGeneratorAgent",
    "StaticCheckerAgent",
    "DocAssemblerAgent",
]

from aurora.agents.architecture_lookup import ArchitectureLookupAgent
from aurora.agents.base import BaseAgent
from aurora.agents.code_generator import CodeGeneratorAgent
from aurora.agents.doc_assembler import DocAssemblerAgent
from aurora.agents.feature_designer import FeatureDesignerAgent
from aurora.agents.request_parser import RequestParserAgent
from aurora.agents.static_checker import StaticCheckerAgent
from aurora.agents.task_planner import TaskPlannerAgent
