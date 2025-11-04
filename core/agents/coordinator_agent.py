"""
Coordinator Agent
Orchestrates the multi-agent research workflow
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_agent import BaseAgent, AgentRole, Task, Message, MessageType


logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent: Orchestrates research workflow
    
    Responsibilities:
    - Accept research queries from users
    - Break down queries into subtasks
    - Assign tasks to specialized agents
    - Monitor progress and handle errors
    - Synthesize final results
    """
    
    def __init__(self, agent_id: str = "coordinator", llm_config: Optional[Dict] = None):
        """Initialize Coordinator Agent"""
        super().__init__(agent_id, AgentRole.COORDINATOR, llm_config)
        
        # Track registered agents
        self.registered_agents: Dict[str, Dict] = {}
        
        # Track ongoing research workflows
        self.active_workflows: Dict[str, Dict] = {}
        
        self.logger.info("Coordinator Agent initialized")
    
    def register_agent(self, agent_id: str, role: AgentRole, capabilities: List[str]):
        """
        Register a specialized agent
        
        Args:
            agent_id: Agent identifier
            role: Agent role
            capabilities: List of agent capabilities
        """
        self.registered_agents[agent_id] = {
            'role': role.value,
            'capabilities': capabilities,
            'status': 'available'
        }
        self.logger.info(f"Registered agent {agent_id} with role {role.value}")
    
    async def process_task(self, task: Task) -> Any:
        """
        Process coordinator tasks
        
        Args:
            task: Task to process
            
        Returns:
            Task result
        """
        if task.task_type == "research_query":
            return await self._handle_research_query(task)
        elif task.task_type == "synthesize_results":
            return await self._synthesize_results(task)
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")
    
    async def _handle_research_query(self, task: Task) -> Dict:
        """
        Handle a research query by breaking it down and delegating
        
        Args:
            task: Research query task
            
        Returns:
            Workflow information
        """
        query = task.parameters.get('query', '')
        workflow_id = task.parameters.get('workflow_id', f"workflow_{datetime.now().timestamp()}")
        
        self.logger.info(f"Processing research query: {query}")
        
        # Create workflow
        workflow = {
            'workflow_id': workflow_id,
            'query': query,
            'status': 'in_progress',
            'subtasks': [],
            'results': {},
            'started_at': datetime.now()
        }
        
        self.active_workflows[workflow_id] = workflow
        
        # Break down into subtasks
        subtasks = self._plan_research_workflow(query)
        
        # Assign subtasks to agents
        for subtask in subtasks:
            assigned_agent = self._select_agent(subtask['required_capability'])
            
            if assigned_agent:
                subtask['assigned_to'] = assigned_agent
                workflow['subtasks'].append(subtask)
                
                # Send task to agent
                self.send_message(
                    recipient=assigned_agent,
                    message_type=MessageType.TASK_REQUEST,
                    content={
                        'task_id': subtask['task_id'],
                        'task_type': subtask['task_type'],
                        'description': subtask['description'],
                        'parameters': subtask['parameters'],
                        'workflow_id': workflow_id
                    }
                )
                
                self.logger.info(f"Assigned subtask {subtask['task_id']} to {assigned_agent}")
            else:
                self.logger.warning(f"No agent available for capability: {subtask['required_capability']}")
        
        return workflow
    
    def _plan_research_workflow(self, query: str) -> List[Dict]:
        """
        Plan research workflow by breaking query into subtasks
        
        Args:
            query: Research query
            
        Returns:
            List of subtasks
        """
        # Simple planning logic (can be enhanced with LLM)
        subtasks = []
        
        # Step 1: Data Collection
        subtasks.append({
            'task_id': f"collect_{datetime.now().timestamp()}",
            'task_type': 'collect_papers',
            'description': f"Collect research papers for query: {query}",
            'parameters': {'query': query, 'max_results': 20},
            'required_capability': 'data_collection',
            'priority': 3
        })
        
        # Step 2: Analysis
        subtasks.append({
            'task_id': f"analyze_{datetime.now().timestamp()}",
            'task_type': 'analyze_papers',
            'description': f"Analyze collected papers for query: {query}",
            'parameters': {'query': query},
            'required_capability': 'analysis',
            'priority': 2
        })
        
        # Step 3: Report Generation
        subtasks.append({
            'task_id': f"report_{datetime.now().timestamp()}",
            'task_type': 'generate_report',
            'description': f"Generate research report for query: {query}",
            'parameters': {'query': query},
            'required_capability': 'report_writing',
            'priority': 1
        })
        
        return subtasks
    
    def _select_agent(self, required_capability: str) -> Optional[str]:
        """
        Select best agent for a capability
        
        Args:
            required_capability: Required capability
            
        Returns:
            Agent ID or None
        """
        for agent_id, agent_info in self.registered_agents.items():
            if required_capability in agent_info['capabilities']:
                if agent_info['status'] == 'available':
                    return agent_id
        
        return None
    
    async def _synthesize_results(self, task: Task) -> Dict:
        """
        Synthesize results from multiple agents
        
        Args:
            task: Synthesis task
            
        Returns:
            Synthesized results
        """
        workflow_id = task.parameters.get('workflow_id')
        workflow = self.active_workflows.get(workflow_id)
        
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Collect results from all subtasks
        all_results = workflow.get('results', {})
        
        # Simple synthesis (can be enhanced with LLM)
        synthesis = {
            'query': workflow['query'],
            'papers_collected': all_results.get('papers_collected', 0),
            'analysis_summary': all_results.get('analysis_summary', ''),
            'report': all_results.get('report', ''),
            'completed_at': datetime.now()
        }
        
        workflow['status'] = 'completed'
        workflow['synthesis'] = synthesis
        
        self.logger.info(f"Synthesized results for workflow {workflow_id}")
        
        return synthesis
    
    def update_workflow_result(self, workflow_id: str, task_id: str, result: Any):
        """
        Update workflow with task result
        
        Args:
            workflow_id: Workflow identifier
            task_id: Task identifier
            result: Task result
        """
        workflow = self.active_workflows.get(workflow_id)
        
        if workflow:
            workflow['results'][task_id] = result
            
            # Check if all subtasks completed
            completed = sum(1 for st in workflow['subtasks'] 
                          if st['task_id'] in workflow['results'])
            
            if completed == len(workflow['subtasks']):
                # All subtasks done, trigger synthesis
                synthesis_task = Task(
                    task_id=f"synthesize_{workflow_id}",
                    task_type='synthesize_results',
                    description=f"Synthesize results for workflow {workflow_id}",
                    parameters={'workflow_id': workflow_id}
                )
                self.add_task(synthesis_task)
    
    def get_capabilities(self) -> List[str]:
        """Get coordinator capabilities"""
        return [
            'workflow_orchestration',
            'task_planning',
            'agent_coordination',
            'result_synthesis'
        ]
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """
        Get status of a workflow
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow status or None
        """
        workflow = self.active_workflows.get(workflow_id)
        
        if not workflow:
            return None
        
        completed_subtasks = len([st for st in workflow['subtasks'] 
                                 if st['task_id'] in workflow['results']])
        
        return {
            'workflow_id': workflow_id,
            'query': workflow['query'],
            'status': workflow['status'],
            'total_subtasks': len(workflow['subtasks']),
            'completed_subtasks': completed_subtasks,
            'progress': f"{completed_subtasks}/{len(workflow['subtasks'])}"
        }
    
    def get_all_workflows(self) -> List[Dict]:
        """Get all active workflows"""
        return [
            self.get_workflow_status(wf_id) 
            for wf_id in self.active_workflows.keys()
        ]
