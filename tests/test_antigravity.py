import unittest
import asyncio
from src.core.antigravity import AntigravityClient, TaskStatus

class TestAntigravity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = AntigravityClient()

    async def test_get_models(self):
        models = await self.client.get_models()
        self.assertTrue(len(models) > 0)
        self.assertEqual(models[0].id, "gemini-3-pro")

    async def test_workspaces(self):
        ws = await self.client.get_workspaces()
        self.assertTrue(len(ws) > 0)

        new_ws = await self.client.create_workspace("test-ws")
        self.assertEqual(new_ws.name, "test-ws")

    async def test_execute_task(self):
        # We need to iterate over the async generator
        updates = []
        async for task in self.client.execute_task("Do something", "test-ws"):
            updates.append(task)
            # Speed up test by not sleeping?
            # The mock sleeps.
            # We can monkeypatch asyncio.sleep if needed, but 1-3s is fine for a few steps.
            pass

        self.assertEqual(updates[-1].status, TaskStatus.COMPLETED)
        self.assertEqual(updates[-1].progress, 100)

if __name__ == '__main__':
    unittest.main()
