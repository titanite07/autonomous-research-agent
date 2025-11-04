"""
Agent Communication System
Manages message passing and coordination between agents
"""
import logging
import asyncio
from typing import Dict, List, Optional
from collections import defaultdict

from .base_agent import BaseAgent, Message, MessageType


logger = logging.getLogger(__name__)


class AgentCommunicationSystem:
    """
    Manages communication between agents in the multi-agent system
    """
    
    def __init__(self):
        """Initialize communication system"""
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue: List[Message] = []
        self.is_running = False
        self.logger = logger
    
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the communication system
        
        Args:
            agent: Agent to register
        """
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id} (role: {agent.role.value})")
    
    def unregister_agent(self, agent_id: str):
        """
        Unregister an agent
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
    
    def send_message(self, message: Message):
        """
        Send a message through the communication system
        
        Args:
            message: Message to send
        """
        if message.recipient not in self.agents:
            self.logger.warning(f"Recipient {message.recipient} not found")
            return
        
        recipient_agent = self.agents[message.recipient]
        recipient_agent.receive_message(message)
        
        self.logger.debug(
            f"Delivered message from {message.sender} to {message.recipient} "
            f"(type: {message.message_type.value})"
        )
    
    async def process_agent_outboxes(self):
        """Process outgoing messages from all agents"""
        for agent in self.agents.values():
            while agent.outbox:
                message = agent.outbox.pop(0)
                self.send_message(message)
    
    async def start(self):
        """Start the communication system"""
        self.is_running = True
        self.logger.info("Communication system started")
        
        # Start all registered agents
        tasks = [agent.start() for agent in self.agents.values()]
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop the communication system"""
        self.is_running = False
        self.logger.info("Communication system stopping")
        
        # Stop all agents
        tasks = [agent.stop() for agent in self.agents.values()]
        await asyncio.gather(*tasks)
    
    async def run(self):
        """Main communication loop"""
        await self.start()
        
        while self.is_running:
            # Process outgoing messages
            await self.process_agent_outboxes()
            
            # Small delay
            await asyncio.sleep(0.1)
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get agent by ID
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent or None
        """
        return self.agents.get(agent_id)
    
    def get_agents_by_role(self, role_value: str) -> List[BaseAgent]:
        """
        Get all agents with a specific role
        
        Args:
            role_value: Role value string
            
        Returns:
            List of agents
        """
        return [
            agent for agent in self.agents.values()
            if agent.role.value == role_value
        ]
    
    def get_system_status(self) -> Dict:
        """Get status of the communication system"""
        agent_statuses = {}
        
        for agent_id, agent in self.agents.items():
            agent_statuses[agent_id] = agent.get_status()
        
        return {
            'is_running': self.is_running,
            'total_agents': len(self.agents),
            'agents': agent_statuses
        }
    
    def broadcast_message(
        self,
        sender: str,
        message_type: MessageType,
        content: Dict,
        exclude: Optional[List[str]] = None
    ):
        """
        Broadcast message to all agents
        
        Args:
            sender: Sender agent ID
            message_type: Type of message
            content: Message content
            exclude: Agent IDs to exclude
        """
        exclude = exclude or []
        
        for agent_id in self.agents:
            if agent_id not in exclude and agent_id != sender:
                message = Message(
                    sender=sender,
                    recipient=agent_id,
                    message_type=message_type,
                    content=content
                )
                self.send_message(message)


class MultiAgentOrchestrator:
    """
    High-level orchestrator for multi-agent research workflows
    """
    
    def __init__(self):
        """Initialize orchestrator"""
        self.comm_system = AgentCommunicationSystem()
        self.coordinator: Optional[BaseAgent] = None
        self.logger = logger
    
    def setup_agents(
        self,
        coordinator: BaseAgent,
        data_collector: BaseAgent,
        analyzer: BaseAgent,
        report_writer: BaseAgent
    ):
        """
        Setup all agents in the system
        
        Args:
            coordinator: Coordinator agent
            data_collector: Data collector agent
            analyzer: Analyzer agent
            report_writer: Report writer agent
        """
        # Register all agents
        self.comm_system.register_agent(coordinator)
        self.comm_system.register_agent(data_collector)
        self.comm_system.register_agent(analyzer)
        self.comm_system.register_agent(report_writer)
        
        # Set coordinator
        self.coordinator = coordinator
        
        # Register agents with coordinator
        coordinator.register_agent(
            data_collector.agent_id,
            data_collector.role,
            data_collector.get_capabilities()
        )
        coordinator.register_agent(
            analyzer.agent_id,
            analyzer.role,
            analyzer.get_capabilities()
        )
        coordinator.register_agent(
            report_writer.agent_id,
            report_writer.role,
            report_writer.get_capabilities()
        )
        
        self.logger.info("Multi-agent system setup complete")
    
    async def execute_research_query(self, query: str) -> Dict:
        """
        Execute a research query through the multi-agent system
        
        Args:
            query: Research query
            
        Returns:
            Research results
        """
        if not self.coordinator:
            raise RuntimeError("Coordinator not setup")
        
        self.logger.info(f"Executing research query: {query}")
        
        # Create research task for coordinator
        from .base_agent import Task
        
        task = Task(
            task_id=f"research_{query}",
            task_type="research_query",
            description=f"Research query: {query}",
            parameters={'query': query},
            priority=3
        )
        
        # Add task to coordinator
        self.coordinator.add_task(task)
        
        # Start communication system
        await self.comm_system.start()
        
        # Wait for task completion (simplified - in production would be event-driven)
        max_wait = 300  # 5 minutes timeout
        waited = 0
        
        while waited < max_wait:
            await asyncio.sleep(1)
            waited += 1
            
            # Check if task completed
            if task.status in ['completed', 'failed']:
                break
        
        # Stop communication system
        await self.comm_system.stop()
        
        return {
            'query': query,
            'status': task.status,
            'result': task.result,
            'error': task.error
        }
    
    def get_system_status(self) -> Dict:
        """Get status of the entire multi-agent system"""
        return self.comm_system.get_system_status()
