"""Chat channels module with plugin architecture."""

from weisensebot.channels.base import BaseChannel
from weisensebot.channels.manager import ChannelManager

__all__ = ["BaseChannel", "ChannelManager"]
