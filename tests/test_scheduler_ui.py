import unittest
import asyncio
from unittest.mock import MagicMock
from src.cogs.scheduler import Scheduler
from src.cogs.general import ModelManagementView, ModelButton
from src.core.antigravity import MockAntigravityClient, Model

class TestSchedulerLogic(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = MagicMock()
        self.bot.antigravity = MockAntigravityClient()
        # Scheduler calls start() in init, which needs loop
        self.cog = Scheduler(self.bot)

    async def test_add_job(self):
        # Mock scheduler add_job
        self.cog.scheduler.add_job = MagicMock()
        job_id = "test_job"
        data = {
            "cron": "*/10 * * * *",
            "prompt": "Test Prompt",
            "workspace": "ws-test",
            "channel_id": 12345,
            "enabled": True
        }
        self.cog._add_job_to_scheduler(job_id, data)
        # Verify call
        # args[0] is the func, args[1] is trigger
        # kwargs has id, replace_existing, args
        calls = self.cog.scheduler.add_job.call_args
        self.assertIsNotNone(calls)
        kwargs = calls.kwargs
        self.assertEqual(kwargs['id'], job_id)
        self.assertEqual(kwargs['args'], [12345, "Test Prompt", "ws-test"])

class TestGeneralLogic(unittest.IsolatedAsyncioTestCase):
    async def test_model_view(self):
        # View init needs loop
        client = MockAntigravityClient()
        models = [
            Model("m1", "Model 1", "1.0", [], "Status 1"),
            Model("m2", "Model 2", "2.0", [], "Status 2")
        ]
        current = models[0]
        view = ModelManagementView(client, models, current)

        # Verify buttons created
        # discord.ui.View children are populated
        # We need to access children.
        # But discord.ui.View uses internal state that might require more mocking.
        # Let's see if children are accessible.
        buttons = [item for item in view.children if hasattr(item, 'style')]
        self.assertTrue(len(buttons) >= 2)
        # Check styles
        # First button (ModelButton m1) should be success (green)
        # Second button (ModelButton m2) should be secondary (grey)

        # Note: Order is preserved
        btn1 = buttons[0]
        btn2 = buttons[1]

        import discord
        self.assertEqual(btn1.style, discord.ButtonStyle.success)
        self.assertEqual(btn2.style, discord.ButtonStyle.secondary)

if __name__ == '__main__':
    unittest.main()
