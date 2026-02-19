import asyncio
import uuid
import random
import logging
from dataclasses import dataclass, field
from typing import List, Optional, AsyncGenerator, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Model:
    id: str
    name: str
    version: str
    capabilities: List[str]

@dataclass
class Workspace:
    id: str
    name: str
    path: str
    created_at: str

@dataclass
class TaskResult:
    status: TaskStatus
    output: str
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None

@dataclass
class Task:
    id: str
    prompt: str
    workspace_id: str
    model_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0  # 0 to 100
    current_step: str = "Queued"
    result: Optional[TaskResult] = None

class AntigravityClient:
    def __init__(self):
        self._models = [
            Model("gemini-3-pro", "Gemini 3 Pro", "3.0", ["reasoning", "coding"]),
            Model("gemini-3-flash", "Gemini 3 Flash", "3.0", ["fast", "coding"]),
            Model("claude-sonnet-4.5", "Claude Sonnet 4.5", "4.5", ["reasoning", "coding"]),
            Model("claude-opus-4.6", "Claude Opus 4.6 (Thinking)", "4.6", ["deep-reasoning"]),
            Model("gpt-oss-120b", "GPT-OSS 120B (Medium)", "120B", ["general"]),
        ]
        self._workspaces = [
            Workspace("ws-crypto", "crypto", "/home/user/projects/crypto-bot", "2025-01-10"),
            Workspace("ws-frontend", "frontend", "/home/user/projects/web-app", "2025-02-01"),
            Workspace("ws-backend", "backend", "/home/user/projects/api-server", "2025-02-15"),
        ]
        self._active_tasks: Dict[str, Task] = {}
        self._current_model_id = "claude-opus-4.6"
        self._mode = "planning"  # planning or fast

    async def get_models(self) -> List[Model]:
        return self._models

    async def get_workspaces(self) -> List[Workspace]:
        return self._workspaces

    async def get_workspace_by_name(self, name: str) -> Optional[Workspace]:
        for ws in self._workspaces:
            if ws.name == name:
                return ws
        return None

    async def create_workspace(self, name: str) -> Workspace:
        ws = Workspace(f"ws-{name}", name, f"/home/user/projects/{name}", "2026-02-18")
        self._workspaces.append(ws)
        return ws

    async def set_model(self, model_id: str):
        if any(m.id == model_id for m in self._models):
            self._current_model_id = model_id
        else:
            raise ValueError(f"Model {model_id} not found")

    async def get_current_model(self) -> Model:
        return next(m for m in self._models if m.id == self._current_model_id)

    async def set_mode(self, mode: str):
        if mode in ["planning", "fast"]:
            self._mode = mode
        else:
            raise ValueError("Invalid mode")

    async def get_mode(self) -> str:
        return self._mode

    async def execute_task(self, prompt: str, workspace_name: str, attachments: List[str] = []) -> AsyncGenerator[Task, None]:
        """
        Simulates executing a task on Antigravity.
        Yields the Task object with updated progress.
        """
        workspace = await self.get_workspace_by_name(workspace_name)
        if not workspace:
            workspace = await self.create_workspace(workspace_name)

        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            prompt=prompt,
            workspace_id=workspace.id,
            model_id=self._current_model_id,
            status=TaskStatus.RUNNING
        )
        self._active_tasks[task_id] = task

        logger.info(f"Starting task {task_id} in {workspace_name} with {self._current_model_id}")

        # Simulate steps
        steps = [
            ("Analyzing request...", 10),
            ("Planning execution...", 30),
            ("Generating code...", 60),
            ("Verifying changes...", 80),
            ("Finalizing...", 95),
            ("Completed", 100)
        ]

        # Simulate processing attachments
        if attachments:
            steps.insert(0, (f"Processing {len(attachments)} attachments...", 5))

        for step_name, progress in steps:
            if task.status == TaskStatus.CANCELLED:
                yield task
                return

            await asyncio.sleep(random.uniform(1.0, 3.0)) # Simulate work
            task.current_step = step_name
            task.progress = progress
            yield task

        task.status = TaskStatus.COMPLETED
        task.result = TaskResult(
            status=TaskStatus.COMPLETED,
            output=f"Successfully executed: {prompt}\nModified 3 files.",
            artifacts=["src/main.py", "tests/test_feature.py"]
        )
        yield task

        # Cleanup from active tasks after some time in real app, but here we keep it for status check?
        # For now, keep it.

    async def cancel_task(self, task_id: str) -> bool:
        if task_id in self._active_tasks:
            self._active_tasks[task_id].status = TaskStatus.CANCELLED
            return True
        return False

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        return self._active_tasks.get(task_id)
