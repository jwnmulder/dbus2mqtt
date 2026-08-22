import asyncio
import logging

from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from dbus2mqtt import AppContext
from dbus2mqtt.config import (
    FlowConfig,
    FlowTriggerConfig,
)
from dbus2mqtt.flow.flow_trigger_handlers import FlowTriggerHandler
from dbus2mqtt.flow.flow_trigger_processor import FlowTriggerProcessor

logger = logging.getLogger(__name__)


class FlowScheduler:
    def __init__(self, app_context: AppContext):
        self.config = app_context.config
        self.event_broker = app_context.event_broker
        self.scheduler = AsyncIOScheduler()
        self._trigger_processor = FlowTriggerProcessor(app_context)

    async def _schedule_flow_trigger(self, flow, trigger_config: FlowTriggerConfig):
        await self._trigger_processor.trigger_flow(
            flow, trigger_config, FlowTriggerHandler(trigger_config.type, {})
        )

    async def scheduler_task(self):

        self.scheduler.start()

        # configure global flow trigger
        self.start_flow_set(self.config.flows)

        while True:
            await asyncio.sleep(1000)

    def start_flow_set(self, flows: list[FlowConfig]):
        for flow in flows:
            for trigger in flow.triggers:
                if trigger.type == "schedule":
                    existing_job = self.scheduler.get_job(trigger.id)
                    if existing_job:
                        logger.debug(
                            f"Skipping creation, flow scheduler already exists, id={trigger.id}"
                        )
                    if not existing_job and trigger.type == "schedule":
                        logger.info(f"Starting scheduler[{trigger.id}] for flow {flow.id}")
                        if trigger.interval:
                            trigger_args: dict[str, Any] = trigger.interval
                            # Each schedule gets its own job
                            self.scheduler.add_job(
                                self._schedule_flow_trigger,
                                "interval",
                                id=trigger.id,
                                max_instances=1,
                                misfire_grace_time=5,
                                coalesce=True,
                                args=[flow, trigger],
                                **trigger_args,
                            )
                        elif trigger.cron:
                            trigger_args: dict[str, Any] = trigger.cron
                            # Each schedule gets its own job
                            self.scheduler.add_job(
                                self._schedule_flow_trigger,
                                "cron",
                                id=trigger.id,
                                max_instances=1,
                                misfire_grace_time=5,
                                coalesce=True,
                                args=[flow, trigger],
                                **trigger_args,
                            )

    def stop_flow_set(self, flows: list[FlowConfig]):
        for flow in flows:
            for trigger in flow.triggers:
                if trigger.type == "schedule":
                    logger.info(f"Stopping scheduler[{trigger.id}] for flow {flow.id}")
                    try:
                        self.scheduler.remove_job(trigger.id)
                    except Exception as e:
                        logger.error(
                            f"Error removing scheduled job {trigger.id}, job likely removed before: {e}"
                        )
