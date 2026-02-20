import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import uuid
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

SCHEDULE_FILE = "data/schedules.json"

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.schedules = {}
        self._load_schedules()
        self.scheduler.start()

    def cog_unload(self):
        self.scheduler.shutdown()

    def _load_schedules(self):
        if os.path.exists(SCHEDULE_FILE):
            try:
                with open(SCHEDULE_FILE, 'r') as f:
                    self.schedules = json.load(f)
            except:
                self.schedules = {}

        # Re-schedule all
        for job_id, data in self.schedules.items():
            self._add_job_to_scheduler(job_id, data)

    def _save_schedules(self):
        os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(self.schedules, f, indent=4)

    def _add_job_to_scheduler(self, job_id, data):
        try:
            trigger = CronTrigger.from_crontab(data['cron'])
            job = self.scheduler.add_job(
                self.execute_scheduled_task,
                trigger,
                id=job_id,
                args=[data['channel_id'], data['prompt'], data['workspace']],
                replace_existing=True
            )

            # Check if paused
            if not data.get('enabled', True):
                job.pause()

            logger.info(f"Scheduled job {job_id}: {data['cron']} (Enabled: {data.get('enabled', True)})")
        except Exception as e:
            logger.error(f"Failed to schedule job {job_id}: {e}")

    async def execute_scheduled_task(self, channel_id, prompt, workspace_name):
        channel = self.bot.get_channel(channel_id)
        if not channel:
            logger.warning(f"Channel {channel_id} not found for scheduled task.")
            return

        embed = discord.Embed(
            title="⏰ Scheduled Task Started",
            description=f"Executing: **{prompt}**\nWorkspace: **{workspace_name}**",
            color=discord.Color.purple()
        )
        msg = await channel.send(embed=embed)

        # Execute in Antigravity
        client = self.bot.antigravity

        try:
            async for task_update in client.execute_task(prompt, workspace_name):
                new_embed = discord.Embed(
                    title=f"⏰ Task Status: {task_update.status.value.upper()}",
                    description=f"**Step**: {task_update.current_step}\n**Progress**: {task_update.progress}%",
                    color=discord.Color.orange()
                )
                if task_update.status.value == "completed":
                    new_embed.title = "✅ Scheduled Task Completed"
                    new_embed.color = discord.Color.green()
                    new_embed.description = task_update.result.output

                await msg.edit(embed=new_embed)

        except Exception as e:
            await msg.edit(content=f"❌ Error in scheduled task: {e}")

    @app_commands.command(name="schedule", description="Schedule a recurring task")
    @app_commands.describe(cron="Cron expression (e.g. '*/10 * * * *')", prompt="Task prompt", workspace="Workspace name")
    async def schedule(self, interaction: discord.Interaction, cron: str, prompt: str, workspace: str):
        ws = await self.bot.antigravity.get_workspace_by_name(workspace)
        # We allow scheduling even if workspace check fails strictly (maybe it will exist later),
        # but for now let's assume loose check or warn.

        try:
            CronTrigger.from_crontab(cron)
        except ValueError:
            await interaction.response.send_message("❌ Invalid Cron expression.", ephemeral=True)
            return

        job_id = str(uuid.uuid4())[:8]
        data = {
            "cron": cron,
            "prompt": prompt,
            "workspace": workspace,
            "channel_id": interaction.channel_id,
            "created_at": str(interaction.created_at),
            "enabled": True
        }

        self.schedules[job_id] = data
        self._save_schedules()
        self._add_job_to_scheduler(job_id, data)

        embed = discord.Embed(title="📅 Schedule Created", color=discord.Color.green())
        embed.add_field(name="ID", value=job_id)
        embed.add_field(name="Cron", value=f"`{cron}`")
        embed.add_field(name="Prompt", value=prompt)
        embed.add_field(name="Workspace", value=workspace)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="schedules", description="List or manage schedules")
    async def schedules(self, interaction: discord.Interaction):
        if not self.schedules:
            await interaction.response.send_message("No active schedules.", ephemeral=True)
            return

        embed = discord.Embed(title="🗓️ Active Schedules", color=discord.Color.blue())
        for jid, data in self.schedules.items():
            status = "🟢 Running" if data.get('enabled', True) else "⏸️ Paused"
            val = f"**Status**: {status}\n**Cron**: `{data['cron']}`\n**Workspace**: {data['workspace']}\n**Prompt**: {data['prompt']}"
            embed.add_field(name=f"ID: {jid}", value=val, inline=False)

        view = ScheduleView(self, self.schedules)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def delete_schedule(self, job_id: str):
        if job_id in self.schedules:
            del self.schedules[job_id]
            self._save_schedules()
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            return True
        return False

    async def toggle_schedule(self, job_id: str):
        if job_id in self.schedules:
            current = self.schedules[job_id].get('enabled', True)
            self.schedules[job_id]['enabled'] = not current
            self._save_schedules()

            job = self.scheduler.get_job(job_id)
            if job:
                if self.schedules[job_id]['enabled']:
                    job.resume()
                else:
                    job.pause()
            return True
        return False

class ScheduleActionView(discord.ui.View):
    def __init__(self, cog, job_id):
        super().__init__()
        self.cog = cog
        self.job_id = job_id

        data = cog.schedules.get(job_id)
        is_enabled = data and data.get('enabled', True)

        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "toggle":
                if is_enabled:
                    child.label = "Pause"
                    child.style = discord.ButtonStyle.secondary
                else:
                    child.label = "Resume"
                    child.style = discord.ButtonStyle.success
                break

    @discord.ui.button(custom_id="toggle", label="Pause/Resume", style=discord.ButtonStyle.primary)
    async def toggle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.toggle_schedule(self.job_id)
        # Update button
        data = self.cog.schedules.get(self.job_id)
        if data and data.get('enabled', True):
             button.label = "Pause"
             button.style = discord.ButtonStyle.secondary
             await interaction.response.edit_message(content=f"✅ Resumed schedule {self.job_id}", view=self)
        elif data:
             button.label = "Resume"
             button.style = discord.ButtonStyle.success
             await interaction.response.edit_message(content=f"⏸️ Paused schedule {self.job_id}", view=self)
        else:
             await interaction.response.edit_message(content="❌ Schedule no longer exists.", view=None)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.delete_schedule(self.job_id)
        await interaction.response.edit_message(content=f"🗑️ Deleted schedule {self.job_id}", view=None)

class ScheduleSelect(discord.ui.Select):
    def __init__(self, cog, schedules):
        options = []
        for jid, data in schedules.items():
            status = "🟢" if data.get('enabled', True) else "⏸️"
            label = f"{status} {jid}"
            desc = f"{data['workspace']}: {data['prompt'][:30]}"
            options.append(discord.SelectOption(label=label, value=jid, description=desc))

        super().__init__(placeholder="Select a schedule to manage...", options=options)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        job_id = self.values[0]
        data = self.cog.schedules.get(job_id)
        if not data:
             await interaction.response.send_message("❌ Schedule not found.", ephemeral=True)
             return

        view = ScheduleActionView(self.cog, job_id)
        status = "Running" if data.get('enabled', True) else "Paused"
        content = f"**Managing Schedule {job_id}**\nStatus: {status}\nPrompt: {data['prompt']}\nCron: `{data['cron']}`"
        await interaction.response.send_message(content, view=view, ephemeral=True)

class ScheduleView(discord.ui.View):
    def __init__(self, cog, schedules):
        super().__init__()
        if schedules:
            self.add_item(ScheduleSelect(cog, schedules))

async def setup(bot):
    await bot.add_cog(Scheduler(bot))
