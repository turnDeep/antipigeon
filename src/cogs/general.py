import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from typing import List, Optional

from src.core.antigravity import BaseAntigravityClient, TaskStatus, Model

logger = logging.getLogger(__name__)

TEMPLATE_FILE = "data/templates.json"

class ModelButton(discord.ui.Button):
    def __init__(self, model: Model, is_selected: bool):
        super().__init__(
            style=discord.ButtonStyle.success if is_selected else discord.ButtonStyle.secondary,
            label=model.name[:80], # Limit label length just in case
            custom_id=f"select_model_{model.id}"
        )
        self.model_id = model.id

    async def callback(self, interaction: discord.Interaction):
        # Determine the view to access the client
        view: ModelManagementView = self.view

        # Set new model
        try:
            await view.client.set_model(self.model_id)
            # Refresh the UI
            await view.refresh_ui(interaction)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting model: {e}", ephemeral=True)

class RefreshButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="更新",
            emoji="🔄",
            custom_id="refresh_models",
            row=4
        )

    async def callback(self, interaction: discord.Interaction):
        view: ModelManagementView = self.view
        await view.refresh_ui(interaction)

class ModelManagementView(discord.ui.View):
    def __init__(self, client: BaseAntigravityClient, models: List[Model], current_model: Model):
        super().__init__(timeout=None) # Persistent view if needed, but for now just standard
        self.client = client
        self.models = models
        self.current_model = current_model

        # Add buttons for each model
        for model in models:
            is_selected = (model.id == current_model.id)
            self.add_item(ModelButton(model, is_selected))

        # Add refresh button
        self.add_item(RefreshButton())

    async def refresh_ui(self, interaction: discord.Interaction):
        # Fetch latest state
        self.models = await self.client.get_models()
        self.current_model = await self.client.get_current_model()

        # Rebuild view
        self.clear_items()
        for model in self.models:
            is_selected = (model.id == self.current_model.id)
            self.add_item(ModelButton(model, is_selected))
        self.add_item(RefreshButton())

        # Rebuild embed
        embed = self.create_embed()

        # Update message
        await interaction.response.edit_message(embed=embed, view=self)

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title="🤖 モデル管理", color=discord.Color.dark_theme())

        # Current Model Status
        # Assuming status_text contains something like "🟢 100% ⏳ 4h 59m"
        status = self.current_model.status_text
        embed.description = f"**現在のモデル**: {self.current_model.name} ({status})"

        # Available Models List
        models_desc = ""
        for m in self.models:
            icon = "✅" if m.id == self.current_model.id else "⬜"
            # Format: ⬜ Gemini 3 Pro (High) 🟢 100% ⏳ 4h 59m
            models_desc += f"{icon} {m.name} {m.status_text}\n"

        embed.add_field(name=f"📋 利用可能なモデル ({len(self.models)}件)", value=models_desc, inline=False)
        embed.set_footer(text=f"Updated at {discord.utils.utcnow().strftime('%H:%M')}")
        return embed

class TemplateRunSelect(discord.ui.Select):
    def __init__(self, cog, templates, workspace):
        options = []
        for name, content in templates.items():
            desc = content[:50] + "..." if len(content) > 50 else content
            options.append(discord.SelectOption(label=name, description=desc, value=name))

        super().__init__(placeholder="Select a template to run...", min_values=1, max_values=1, options=options)
        self.cog = cog
        self.templates = templates
        self.workspace = workspace

    async def callback(self, interaction: discord.Interaction):
        name = self.values[0]
        prompt = self.templates[name]
        await interaction.response.send_message(f"🚀 Starting template **{name}** in **{self.workspace.name}**...", ephemeral=True)
        # Execute
        await self.cog.execute_template_task(interaction.channel, prompt, self.workspace)

class TemplateRunView(discord.ui.View):
    def __init__(self, cog, templates, workspace):
        super().__init__()
        self.add_item(TemplateRunSelect(cog, templates, workspace))

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antigravity = bot.antigravity
        self._load_templates()

    def _load_templates(self):
        if os.path.exists(TEMPLATE_FILE):
            try:
                with open(TEMPLATE_FILE, 'r') as f:
                    self.templates = json.load(f)
            except:
                self.templates = {}
        else:
            self.templates = {}

    def _save_templates(self):
        os.makedirs(os.path.dirname(TEMPLATE_FILE), exist_ok=True)
        with open(TEMPLATE_FILE, 'w') as f:
            json.dump(self.templates, f, indent=4)

    async def execute_template_task(self, channel, prompt, workspace):
        # Create initial embed
        embed = discord.Embed(
            title="🕊️ Antipigeon Template Task",
            description=f"Processing template for workspace **{workspace.name}**...",
            color=discord.Color.blue()
        )
        embed.add_field(name="Prompt", value=prompt[:1000], inline=False)

        message = await channel.send(embed=embed)

        try:
            async for task_update in self.antigravity.execute_task(prompt, workspace.name):
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

                await message.edit(embed=new_embed)
        except Exception as e:
            logger.error(f"Error executing template task: {e}")
            await message.edit(content=f"❌ Error: {e}")

    @app_commands.command(name="models", description="List and switch AI models")
    async def models(self, interaction: discord.Interaction):
        models = await self.antigravity.get_models()
        current = await self.antigravity.get_current_model()

        view = ModelManagementView(self.antigravity, models, current)
        embed = view.create_embed()

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="mode", description="Switch execution mode (Planning/Fast)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Planning (Slower, better reasoning)", value="planning"),
        app_commands.Choice(name="Fast (Quicker, for simple tasks)", value="fast")
    ])
    async def mode(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        await self.antigravity.set_mode(mode.value)
        await interaction.response.send_message(f"⚙️ Mode switched to **{mode.name}**", ephemeral=True)

    @app_commands.command(name="workspaces", description="List Antigravity workspaces")
    async def workspaces(self, interaction: discord.Interaction):
        wss = await self.antigravity.get_workspaces()
        embed = discord.Embed(title="📁 Workspaces", color=discord.Color.green())

        desc = ""
        for ws in wss:
            desc += f"**{ws.name}** (`{ws.path}`)\nID: {ws.id}\nCreated: {ws.created_at}\n\n"

        embed.description = desc or "No workspaces found."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="Check system status")
    async def status(self, interaction: discord.Interaction):
        current_model = await self.antigravity.get_current_model()
        mode = await self.antigravity.get_mode()

        embed = discord.Embed(title="📊 System Status", color=discord.Color.teal())
        embed.add_field(name="Model", value=current_model.name, inline=True)
        embed.add_field(name="Mode", value=mode.capitalize(), inline=True)
        embed.add_field(name="Antigravity Connection", value="Active 🟢", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="templates", description="Manage prompt templates")
    @app_commands.describe(action="list/add/remove/run", name="Template name", content="Template content (for add)")
    @app_commands.choices(action=[
        app_commands.Choice(name="List", value="list"),
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove"),
        app_commands.Choice(name="Run", value="run")
    ])
    async def templates(self, interaction: discord.Interaction, action: app_commands.Choice[str], name: Optional[str] = None, content: Optional[str] = None):
        if action.value == "list":
            if not self.templates:
                await interaction.response.send_message("No templates saved.", ephemeral=True)
                return

            embed = discord.Embed(title="📝 Templates", color=discord.Color.gold())
            for n, c in self.templates.items():
                embed.add_field(name=n, value=c[:100] + ("..." if len(c) > 100 else ""), inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action.value == "add":
            if not name or not content:
                await interaction.response.send_message("❌ Name and content required for adding.", ephemeral=True)
                return
            self.templates[name] = content
            self._save_templates()
            await interaction.response.send_message(f"✅ Template **{name}** added.", ephemeral=True)

        elif action.value == "remove":
            if not name:
                 await interaction.response.send_message("❌ Name required for removal.", ephemeral=True)
                 return
            if name in self.templates:
                del self.templates[name]
                self._save_templates()
                await interaction.response.send_message(f"🗑️ Template **{name}** removed.", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Template **{name}** not found.", ephemeral=True)

        elif action.value == "run":
            if not self.templates:
                await interaction.response.send_message("No templates saved.", ephemeral=True)
                return

            # Identify Workspace
            workspace = None
            if hasattr(interaction.channel, "category") and interaction.channel.category:
                 workspace = await self.antigravity.get_workspace_by_name(interaction.channel.category.name)

            if not workspace:
                await interaction.response.send_message("❌ Please run this command inside a Workspace channel.", ephemeral=True)
                return

            if name:
                 if name in self.templates:
                     prompt = self.templates[name]
                     await interaction.response.send_message(f"🚀 Starting template **{name}**...", ephemeral=True)
                     await self.execute_template_task(interaction.channel, prompt, workspace)
                 else:
                     await interaction.response.send_message(f"❌ Template **{name}** not found.", ephemeral=True)
            else:
                view = TemplateRunView(self, self.templates, workspace)
                await interaction.response.send_message("Select a template to run:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(General(bot))
