import logging
import discord

logger = logging.getLogger(__name__)

MAX_TEXT_SIZE = 1024 * 1024  # 1MB

async def process_attachment(attachment: discord.Attachment) -> str:
    """
    Downloads and extracts text content from attachments if possible.
    Returns a string representation of the attachment to be appended to the prompt.
    """
    output = f"\n[Attachment: {attachment.filename} (Type: {attachment.content_type}, Size: {attachment.size} bytes)]\n"

    # Simple whitelist for text-like files
    is_text = False
    if attachment.content_type and (
        attachment.content_type.startswith("text/") or
        attachment.content_type in ["application/json", "application/javascript", "application/xml", "application/yaml"]
    ):
        is_text = True
    elif attachment.filename.lower().endswith(('.py', '.json', '.md', '.txt', '.js', '.html', '.css', '.sh', '.yaml', '.yml', '.ts', '.rs', '.go', '.c', '.cpp', '.h')):
        is_text = True

    if is_text:
        if attachment.size > MAX_TEXT_SIZE:
             output += "[Content too large to display inline]\n"
        else:
             try:
                 content = await attachment.read()
                 text = content.decode('utf-8')
                 output += f"--- Begin Content ---\n{text}\n--- End Content ---\n"
             except UnicodeDecodeError:
                 output += "[Binary or non-UTF-8 content]\n"
             except Exception as e:
                 output += f"[Failed to read content: {e}]\n"
    else:
        output += "[Binary file or unsupported type for inline display]\n"

    return output
