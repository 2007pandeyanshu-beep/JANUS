"""JANUS Multi-Agent Scientific Investigation Module (Phase 8)"""

from .types import (
    AgentRole,
    CriticSeverity,
    CriticItem,
    ToolExecutionRecord,
    AgentLogEntry,
    InvestigationInput,
    AgentInvestigationReport,
)
from .tools import (
    LiteratureRetrievalTool,
    ChemicalKineticsTool,
    JanusRankingTool,
    SimplexValidationTool,
)
from .orchestrator import ScientificInvestigationOrchestrator
