import unittest
from unittest.mock import AsyncMock, MagicMock
from src.utils.attachment_handler import process_attachment

class TestAttachmentHandler(unittest.IsolatedAsyncioTestCase):
    async def test_text_attachment(self):
        att = MagicMock()
        att.filename = "test.txt"
        att.content_type = "text/plain"
        att.size = 100
        att.read = AsyncMock(return_value=b"Hello World")

        result = await process_attachment(att)
        self.assertIn("Hello World", result)
        self.assertIn("Begin Content", result)

    async def test_code_attachment(self):
        att = MagicMock()
        att.filename = "script.py"
        att.content_type = None # Sometimes none
        att.size = 50
        att.read = AsyncMock(return_value=b"print('hi')")

        result = await process_attachment(att)
        self.assertIn("print('hi')", result)

    async def test_binary_attachment(self):
        att = MagicMock()
        att.filename = "image.png"
        att.content_type = "image/png"
        att.size = 2000
        att.read = AsyncMock(return_value=b"\x89PNG...")

        result = await process_attachment(att)
        self.assertIn("Binary file or unsupported type", result)
        self.assertNotIn("PNG", result) # Should not dump binary

    async def test_large_file(self):
        att = MagicMock()
        att.filename = "big.txt"
        att.content_type = "text/plain"
        att.size = 10 * 1024 * 1024 # 10MB

        result = await process_attachment(att)
        self.assertIn("Content too large", result)

if __name__ == "__main__":
    unittest.main()
