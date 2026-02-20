import discord
from discord.ext import commands
import logging
import asyncio
import os
from datetime import datetime

from src.core.config import config
from src.core.antigravity import AntigravityClient, TaskStatus
from src.utils.attachment_handler import process_attachment

logger = logging.getLogger(__name__)

class AntipigeonBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.antigravity = AntigravityClient()
        self.start_time = datetime.now()

    async def setup_hook(self):
        # Load extensions
        await self.load_extension("src.cogs.general")
        await self.load_extension("src.cogs.scheduler")

        # Set global interaction check for slash commands
        self.tree.interaction_check = self.interaction_check

        logger.info("Extensions loaded.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("Antipigeon is ready to fly!")

        # Sync commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s).")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        # Sync Workspaces
        await self.sync_workspaces_to_discord()

    async def sync_workspaces_to_discord(self):
        """Creates Discord Categories and Channels for each Antigravity Workspace."""
        workspaces = await self.antigravity.get_workspaces()
        for guild in self.guilds:
            logger.info(f"Syncing workspaces for guild: {guild.name}")
            existing_categories = {c.name: c for c in guild.categories}

            for ws in workspaces:
                category = existing_categories.get(ws.name)
                if not category:
                    try:
                        category = await guild.create_category(ws.name)
                        logger.info(f"Created category '{ws.name}' in guild '{guild.name}'")
                    except Exception as e:
                        logger.error(f"Failed to create category '{ws.name}': {e}")
                        continue

                # Ensure a channel exists
                if not category.channels:
                    try:
                        await category.create_text_channel("chat")
                        logger.info(f"Created channel 'chat' in category '{ws.name}'")
                    except Exception as e:
                        logger.error(f"Failed to create channel in '{ws.name}': {e}")

    async def on_message(self, message: discord.Message):
        # Ignore self
        if message.author.bot:
            return

        # Check allowed users
        if config.allowed_user_ids and message.author.id not in config.allowed_user_ids:
            return

        # Process commands first
        if message.content.startswith(self.command_prefix):
            await self.process_commands(message)
            return

        # Check if in a Workspace Category
        if isinstance(message.channel, discord.TextChannel) and message.channel.category:
            category_name = message.channel.category.name
            workspace = await self.antigravity.get_workspace_by_name(category_name)

            if workspace:
                # This is a workspace task!
                await self.process_workspace_task(message, workspace)
            else:
                pass

    async def process_workspace_task(self, message: discord.Message, workspace):
        prompt = message.content
        attachments = [a.url for a in message.attachments]

        # Parse attachments for content
        attachment_contents = []
        for att in message.attachments:
            try:
                content = await process_attachment(att)
                attachment_contents.append(content)
            except Exception as e:
                logger.error(f"Failed to process attachment {att.filename}: {e}")

        # Check for context (Reply)
        context_text = ""
        if message.reference:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                context_text = f"--- Context from previous message by {ref_msg.author.name} ---\n"
                context_text += ref_msg.content + "\n"
                if ref_msg.embeds:
                    for embed in ref_msg.embeds:
                         context_text += f"[Embed Title]: {embed.title}\n"
                         context_text += f"[Embed Description]: {embed.description}\n"
                         for field in embed.fields:
                             context_text += f"[{field.name}]: {field.value}\n"
                context_text += "--- End Context ---\n\n"
            except Exception as e:
                logger.warning(f"Failed to fetch context message: {e}")

        full_prompt = context_text + prompt
        if attachment_contents:
            full_prompt += "\n" + "".join(attachment_contents)

        if not prompt and not attachments and not context_text:
            return

        # Reply with initial status
        embed = discord.Embed(
            title="🕊️ Antipigeon Task Received",
            description=f"Processing task for workspace **{workspace.name}**...",
            color=discord.Color.blue()
        )
        embed.add_field(name="Prompt", value=prompt[:1000] if prompt else "(No text)", inline=False)
        if context_text:
             embed.add_field(name="Context", value="Included from reply.", inline=False)
        if attachments:
            embed.add_field(name="Attachments", value="\n".join(attachments), inline=False)

        reply_msg = await message.reply(embed=embed)

        # Execute
        try:
            async for task_update in self.antigravity.execute_task(full_prompt, workspace.name, attachments):
                # Update Embed based on progress
                new_embed = discord.Embed(
                    title=f"🕊️ Task Status: {task_update.status.value.upper()}",
                    description=f"**Step**: {task_update.current_step}\n**Progress**: {task_update.progress}%",
                    color=discord.Color.orange() if task_update.status == TaskStatus.RUNNING else discord.Color.green()
                )
                if task_update.status == TaskStatus.COMPLETED:
                    new_embed.title = "✅ Task Completed"
                    new_embed.description = task_update.result.output
                    if task_update.result.artifacts:
                        files_str = "\n".join([f"`{f}`" for f in task_update.result.artifacts])
                        new_embed.add_field(name="Artifacts", value=files_str, inline=False)

                elif task_update.status == TaskStatus.FAILED:
                     new_embed.title = "❌ Task Failed"
                     new_embed.color = discord.Color.red()
                     new_embed.description = f"Error: {task_update.result.error}"

                await reply_msg.edit(embed=new_embed)

        except Exception as e:
            logger.error(f"Error executing task: {e}")
            error_embed = discord.Embed(
                title="❌ Internal Error",
                description=str(e),
                color=discord.Color.red()
            )
            await reply_msg.edit(embed=error_embed)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Global check for application commands (slash commands)."""
        if config.allowed_user_ids and interaction.user.id not in config.allowed_user_ids:
            await interaction.response.send_message("❌ Unauthorized access.", ephemeral=True)
            return False
        return True

bot = AntipigeonBot()

if __name__ == "__main__":
    if not config.token:
        logger.error("No token found! Please run `python src/setup_token.py` or set DISCORD_TOKEN env var.")
        exit(1)

    try:
        bot.run(config.token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
