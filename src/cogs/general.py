import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from typing import List, Optional

from src.core.antigravity import AntigravityClient

logger = logging.getLogger(__name__)

TEMPLATE_FILE = "data/templates.json"

class ModelSelect(discord.ui.Select):
    def __init__(self, models):
        options = [
            discord.SelectOption(
                label=m.name,
                value=m.id,
                description=f"v{m.version} - {', '.join(m.capabilities)}"
            ) for m in models
        ]
        super().__init__(placeholder="Select a model...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        selected_id = self.values[0]
        await view.client.set_model(selected_id)
        current_model = await view.client.get_current_model()
        await interaction.response.send_message(f"✅ Switched to model: **{current_model.name}**", ephemeral=True)

class ModelView(discord.ui.View):
    def __init__(self, client: AntigravityClient, models):
        super().__init__()
        self.client = client
        self.add_item(ModelSelect(models))

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

    @app_commands.command(name="models", description="List and switch AI models")
    async def models(self, interaction: discord.Interaction):
        models = await self.antigravity.get_models()
        current = await self.antigravity.get_current_model()

        embed = discord.Embed(title="🤖 Model Management", color=discord.Color.blue())
        desc = f"**Current Model**: {current.name} (v{current.version})\n\n**Available Models**:"
        for m in models:
            check = "✅" if m.id == current.id else "⬜"
            desc += f"\n{check} **{m.name}** ({', '.join(m.capabilities)})"

        embed.description = desc
        view = ModelView(self.antigravity, models)
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
    @app_commands.describe(action="list/add/remove", name="Template name", content="Template content (for add)")
    @app_commands.choices(action=[
        app_commands.Choice(name="List", value="list"),
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove")
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

async def setup(bot):
    await bot.add_cog(General(bot))
