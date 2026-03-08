"""Message bus module for decoupled channel-agent communication."""

from weisensebot.bus.events import InboundMessage, OutboundMessage
from weisensebot.bus.queue import MessageBus

__all__ = ["MessageBus", "InboundMessage", "OutboundMessage"]
