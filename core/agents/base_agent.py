"""
Base Agent Framework
Defines the base agent class and common functionality for all agents
"""
import logging
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in the multi-agent system"""
    COORDINATOR = "coordinator"
    DATA_COLLECTOR = "data_collector"
    ANALYZER = "analyzer"
    REPORT_WRITER = "report_writer"


class MessageType(Enum):
    """Types of messages agents can send"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    QUERY = "query"
    ERROR = "error"
    COMPLETION = "completion"


@dataclass
class Message:
    """Message passed between agents"""
    sender: str
    recipient: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: Optional[str] = None
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = f"{self.sender}_{self.timestamp.timestamp()}"


@dataclass
class Task:
    """Task to be executed by an agent"""
    task_id: str
    task_type: str
    description: str
    parameters: Dict[str, Any]
    priority: int = 1
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class AgentMemory:
    """Memory system for agents to store and retrieve information"""
    
    def __init__(self, max_size: int = 100):
        """
        Initialize agent memory
        
        Args:
            max_size: Maximum number of items to store
        """
        self.max_size = max_size
        self.short_term: List[Dict] = []
        self.long_term: Dict[str, Any] = {}
        self.working_memory: Dict[str, Any] = {}
    
    def add_to_short_term(self, item: Dict):
        """Add item to short-term memory"""
        self.short_term.append(item)
        if len(self.short_term) > self.max_size:
            # Move oldest to long-term if important
            old_item = self.short_term.pop(0)
            if old_item.get('important', False):
                key = f"item_{len(self.long_term)}"
                self.long_term[key] = old_item
    
    def store_long_term(self, key: str, value: Any):
        """Store item in long-term memory"""
        self.long_term[key] = value
    
    def retrieve_long_term(self, key: str) -> Optional[Any]:
        """Retrieve item from long-term memory"""
        return self.long_term.get(key)
    
    def set_working(self, key: str, value: Any):
        """Set item in working memory"""
        self.working_memory[key] = value
    
    def get_working(self, key: str) -> Optional[Any]:
        """Get item from working memory"""
        return self.working_memory.get(key)
    
    def clear_working(self):
        """Clear working memory"""
        self.working_memory.clear()
    
    def get_recent_context(self, n: int = 5) -> List[Dict]:
        """Get n most recent items from short-term memory"""
        return self.short_term[-n:] if self.short_term else []


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        llm_config: Optional[Dict] = None
    ):
        """
        Initialize base agent
        
        Args:
            agent_id: Unique identifier for the agent
            role: Agent's role in the system
            llm_config: Configuration for LLM integration
        """
        self.agent_id = agent_id
        self.role = role
        self.llm_config = llm_config or {}
        
        # Agent state
        self.is_active = False
        self.current_task: Optional[Task] = None
        self.task_queue: List[Task] = []
        
        # Communication
        self.inbox: List[Message] = []
        self.outbox: List[Message] = []
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # Memory
        self.memory = AgentMemory()
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Register default message handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register default message handlers"""
        self.message_handlers[MessageType.TASK_REQUEST] = self._handle_task_request
        self.message_handlers[MessageType.QUERY] = self._handle_query
        self.message_handlers[MessageType.ERROR] = self._handle_error
    
    # Abstract methods to be implemented by subclasses
    
    @abstractmethod
    async def process_task(self, task: Task) -> Any:
        """
        Process a task assigned to this agent
        
        Args:
            task: Task to process
            
        Returns:
            Task result
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of capabilities this agent has
        
        Returns:
            List of capability names
        """
        pass
    
    # Task management
    
    def add_task(self, task: Task):
        """Add task to agent's queue"""
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        self.logger.info(f"Task {task.task_id} added to queue (priority: {task.priority})")
    
    async def execute_next_task(self) -> Optional[Task]:
        """Execute the next task in queue"""
        if not self.task_queue:
            return None
        
        task = self.task_queue.pop(0)
        self.current_task = task
        task.status = "in_progress"
        
        self.logger.info(f"Executing task {task.task_id}: {task.description}")
        
        try:
            result = await self.process_task(task)
            task.status = "completed"
            task.result = result
            task.completed_at = datetime.now()
            self.logger.info(f"Task {task.task_id} completed successfully")
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.logger.error(f"Task {task.task_id} failed: {e}")
        
        finally:
            self.current_task = None
        
        return task
    
    # Communication
    
    def send_message(self, recipient: str, message_type: MessageType, content: Dict):
        """Send message to another agent"""
        message = Message(
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            content=content
        )
        self.outbox.append(message)
        self.logger.debug(f"Sent {message_type.value} to {recipient}")
    
    def receive_message(self, message: Message):
        """Receive message from another agent"""
        self.inbox.append(message)
        self.logger.debug(f"Received {message.message_type.value} from {message.sender}")
    
    async def process_messages(self):
        """Process all messages in inbox"""
        while self.inbox:
            message = self.inbox.pop(0)
            handler = self.message_handlers.get(message.message_type)
            
            if handler:
                try:
                    await handler(message)
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
            else:
                self.logger.warning(f"No handler for message type: {message.message_type}")
    
    # Default message handlers
    
    async def _handle_task_request(self, message: Message):
        """Handle task request message"""
        task_data = message.content
        task = Task(
            task_id=task_data.get('task_id', f"task_{datetime.now().timestamp()}"),
            task_type=task_data.get('task_type', 'unknown'),
            description=task_data.get('description', ''),
            parameters=task_data.get('parameters', {}),
            priority=task_data.get('priority', 1)
        )
        self.add_task(task)
    
    async def _handle_query(self, message: Message):
        """Handle query message"""
        query = message.content.get('query', '')
        response = await self.answer_query(query)
        
        self.send_message(
            recipient=message.sender,
            message_type=MessageType.TASK_RESPONSE,
            content={'query': query, 'response': response}
        )
    
    async def _handle_error(self, message: Message):
        """Handle error message"""
        error = message.content.get('error', '')
        self.logger.error(f"Received error from {message.sender}: {error}")
    
    async def answer_query(self, query: str) -> str:
        """
        Answer a query (can be overridden by subclasses)
        
        Args:
            query: Query string
            
        Returns:
            Answer string
        """
        return f"Query received: {query}"
    
    # Agent lifecycle
    
    async def start(self):
        """Start the agent"""
        self.is_active = True
        self.logger.info(f"Agent {self.agent_id} started")
    
    async def stop(self):
        """Stop the agent"""
        self.is_active = False
        self.logger.info(f"Agent {self.agent_id} stopped")
    
    async def run(self):
        """Main agent loop"""
        await self.start()
        
        while self.is_active:
            # Process messages
            await self.process_messages()
            
            # Execute tasks
            if self.task_queue:
                await self.execute_next_task()
            
            # Small delay to prevent busy-waiting
            await asyncio.sleep(0.1)
    
    # Utility methods
    
    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            'agent_id': self.agent_id,
            'role': self.role.value,
            'is_active': self.is_active,
            'current_task': self.current_task.task_id if self.current_task else None,
            'queue_size': len(self.task_queue),
            'inbox_size': len(self.inbox),
            'capabilities': self.get_capabilities()
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.agent_id} role={self.role.value}>"
