import asyncio
import uuid
import random
import logging
import json
import aiohttp
from abc import ABC, abstractmethod
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
    status_text: str = "" # e.g. "🟢 100% ⏳ 4h 59m"

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

class BaseAntigravityClient(ABC):
    @abstractmethod
    async def get_models(self) -> List[Model]:
        pass

    @abstractmethod
    async def get_workspaces(self) -> List[Workspace]:
        pass

    @abstractmethod
    async def get_workspace_by_name(self, name: str) -> Optional[Workspace]:
        pass

    @abstractmethod
    async def create_workspace(self, name: str) -> Workspace:
        pass

    @abstractmethod
    async def set_model(self, model_id: str):
        pass

    @abstractmethod
    async def get_current_model(self) -> Model:
        pass

    @abstractmethod
    async def set_mode(self, mode: str):
        pass

    @abstractmethod
    async def get_mode(self) -> str:
        pass

    @abstractmethod
    async def execute_task(self, prompt: str, workspace_name: str, attachments: List[str] = []) -> AsyncGenerator[Task, None]:
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        pass

class MockAntigravityClient(BaseAntigravityClient):
    def __init__(self):
        self._models = [
            Model("gemini-3-pro-high", "Gemini 3 Pro (High)", "3.0", ["high-res", "coding"], "🟢 100% ⏳ 4h 59m"),
            Model("gemini-3-pro-low", "Gemini 3 Pro (Low)", "3.0", ["fast", "coding"], "🟢 100% ⏳ 4h 59m"),
            Model("gemini-3-flash", "Gemini 3 Flash", "3.0", ["flash", "coding"], "🟢 100% ⏳ 4h 59m"),
            Model("claude-sonnet-4.5", "Claude Sonnet 4.5", "4.5", ["reasoning"], "🟡 40% ⏳ 26m"),
            Model("claude-sonnet-4.5-think", "Claude Sonnet 4.5 (Thinking)", "4.5", ["thinking"], "🟡 40% ⏳ 26m"),
            Model("claude-sonnet-4.6", "Claude Sonnet 4.6", "4.6", ["reasoning"], "🟡 40% ⏳ 26m"),
            Model("claude-opus-4.6-think", "Claude Opus 4.6 (Thinking)", "4.6", ["deep-thinking"], "🟡 40% ⏳ 26m"),
            Model("gpt-oss-120b-med", "GPT-OSS 120B (Medium)", "120B", ["general"], "🟡 40% ⏳ 26m"),
        ]
        self._workspaces = [
            Workspace("ws-crypto", "crypto", "/home/user/projects/crypto-bot", "2025-01-10"),
            Workspace("ws-frontend", "frontend", "/home/user/projects/web-app", "2025-02-01"),
            Workspace("ws-backend", "backend", "/home/user/projects/api-server", "2025-02-15"),
        ]
        self._active_tasks: Dict[str, Task] = {}
        self._current_model_id = "claude-opus-4.6-think"
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

    async def cancel_task(self, task_id: str) -> bool:
        if task_id in self._active_tasks:
            self._active_tasks[task_id].status = TaskStatus.CANCELLED
            return True
        return False

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        return self._active_tasks.get(task_id)

class HttpAntigravityClient(BaseAntigravityClient):
    """
    Real implementation connecting to an Antigravity instance via HTTP API.
    Since Google Antigravity is in preview, this assumes a standard RESTful structure.
    Adjust endpoints as needed.
    """
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip("/")
        self._session = None
        self._current_model_id = "default-model" # Fallback if API doesn't persist state
        self._mode = "planning"

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_models(self) -> List[Model]:
        try:
            session = await self._get_session()
            async with session.get(f"{self.api_url}/models") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [Model(**item) for item in data]
                else:
                    logger.error(f"Failed to fetch models: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Error connecting to Antigravity API: {e}")
            return []

    async def get_workspaces(self) -> List[Workspace]:
        try:
            session = await self._get_session()
            async with session.get(f"{self.api_url}/workspaces") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [Workspace(**item) for item in data]
                return []
        except Exception as e:
            logger.error(f"Error fetching workspaces: {e}")
            return []

    async def get_workspace_by_name(self, name: str) -> Optional[Workspace]:
        wss = await self.get_workspaces()
        for ws in wss:
            if ws.name == name:
                return ws
        return None

    async def create_workspace(self, name: str) -> Workspace:
        session = await self._get_session()
        async with session.post(f"{self.api_url}/workspaces", json={"name": name}) as resp:
            if resp.status == 201:
                data = await resp.json()
                return Workspace(**data)
            raise Exception(f"Failed to create workspace: {resp.status}")

    async def set_model(self, model_id: str):
        session = await self._get_session()
        async with session.post(f"{self.api_url}/config/model", json={"model_id": model_id}) as resp:
            if resp.status == 200:
                self._current_model_id = model_id
            else:
                raise ValueError(f"Failed to set model: {resp.status}")

    async def get_current_model(self) -> Model:
        # Optimistic: check local cache or fetch from API
        models = await self.get_models()
        for m in models:
            if m.id == self._current_model_id:
                return m
        # Fallback
        return models[0] if models else Model("unknown", "Unknown", "0", [], "Unknown")

    async def set_mode(self, mode: str):
        session = await self._get_session()
        async with session.post(f"{self.api_url}/config/mode", json={"mode": mode}) as resp:
            if resp.status == 200:
                self._mode = mode
            else:
                raise ValueError(f"Failed to set mode: {resp.status}")

    async def get_mode(self) -> str:
        return self._mode

    async def execute_task(self, prompt: str, workspace_name: str, attachments: List[str] = []) -> AsyncGenerator[Task, None]:
        session = await self._get_session()

        # Prepare payload
        payload = {
            "prompt": prompt,
            "workspace": workspace_name,
            "attachments": attachments,
            "model_id": self._current_model_id,
            "mode": self._mode
        }

        # Streaming request (SSE or JSON lines)
        try:
            async with session.post(f"{self.api_url}/tasks/execute", json=payload) as resp:
                if resp.status != 200:
                    yield Task(id="error", prompt=prompt, workspace_id="", model_id="", status=TaskStatus.FAILED, result=TaskResult(TaskStatus.FAILED, f"API Error: {resp.status}"))
                    return

                # Read lines
                async for line in resp.content:
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode('utf-8'))
                        # Construct Task object from update
                        task = Task(
                            id=data.get("id", "unknown"),
                            prompt=prompt,
                            workspace_id=data.get("workspace_id", ""),
                            model_id=data.get("model_id", ""),
                            status=TaskStatus(data.get("status", "running")),
                            progress=data.get("progress", 0),
                            current_step=data.get("step", ""),
                            result=TaskResult(**data["result"]) if "result" in data else None
                        )
                        yield task
                    except Exception as e:
                        logger.error(f"Error parsing stream line: {e}")
        except Exception as e:
            logger.error(f"Connection error during task execution: {e}")
            yield Task(id="error", prompt=prompt, workspace_id="", model_id="", status=TaskStatus.FAILED, result=TaskResult(TaskStatus.FAILED, str(e)))

    async def cancel_task(self, task_id: str) -> bool:
        session = await self._get_session()
        async with session.post(f"{self.api_url}/tasks/{task_id}/cancel") as resp:
            return resp.status == 200

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        session = await self._get_session()
        async with session.get(f"{self.api_url}/tasks/{task_id}") as resp:
            if resp.status == 200:
                data = await resp.json()
                # Simplified reconstruction
                return Task(
                    id=data["id"],
                    prompt=data["prompt"],
                    workspace_id=data["workspace_id"],
                    model_id=data["model_id"],
                    status=TaskStatus(data["status"]),
                    progress=data["progress"]
                )
        return None

def get_antigravity_client(api_url: Optional[str] = None) -> BaseAntigravityClient:
    if api_url:
        logger.info(f"Using Real Antigravity Client at {api_url}")
        return HttpAntigravityClient(api_url)
    else:
        logger.info("Using Mock Antigravity Client (Simulation Mode)")
        return MockAntigravityClient()
