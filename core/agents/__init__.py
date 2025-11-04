"""
Multi-Agent System Package
Provides agent framework for autonomous research
"""
from .base_agent import (
    BaseAgent,
    AgentRole,
    MessageType,
    Message,
    Task,
    AgentMemory
)
from .coordinator_agent import CoordinatorAgent
from .data_collector_agent import DataCollectorAgent
from .analyzer_agent import AnalyzerAgent
from .report_writer_agent import ReportWriterAgent
from .communication import (
    AgentCommunicationSystem,
    MultiAgentOrchestrator
)

__all__ = [
    'BaseAgent',
    'AgentRole',
    'MessageType',
    'Message',
    'Task',
    'AgentMemory',
    'CoordinatorAgent',
    'DataCollectorAgent',
    'AnalyzerAgent',
    'ReportWriterAgent',
    'AgentCommunicationSystem',
    'MultiAgentOrchestrator'
]
