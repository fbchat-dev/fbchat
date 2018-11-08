from datetime import timedelta

from .core import Core
from ..models import Channel

__all__ = ("ChannelConfiguration",)


class ChannelConfiguration(Core):
    """Contains methods to configure channels"""

    async def archive(self, channel: Channel) -> None:
        """Archive a channel

        Args:
            channel: Channel to archive
        """

    async def unarchive(self, channel: Channel) -> None:
        ...

    async def ignore(self, channel: Channel) -> None:
        """Ignore a channel

        Args:
            channel: Channel to ignore
        """

    async def unignore(self, channel: Channel) -> None:
        """Unignore a channel

        Args:
            channel: Channel to stop ignoring
        """

    async def mute(self, channel: Channel, *, duration: timedelta = None) -> None:
        """Mute a channel for a specific amount of time

        If ``time`` is ``None``, the channel will be muted indefinitely

        Args:
            channel: Channel to mute
            duration: Duration of time to mute channel
        """

    async def unmute(self, channel: Channel) -> None:
        """Unmute a channel

        Args:
            channel: Channel to unmute
        """

    async def mute_reactions(
        self, channel: Channel, *, duration: timedelta = None
    ) -> None:
        """Mute reactions in a channel

        Args:
            channel: Channel to mute reactions in
            duration: Duration of time to mute reactions
        """

    async def unmute_reactions(self, channel: Channel) -> None:
        """Unmute reactions in a channel

        Args:
            channel: Channel to unmute reactions in
        """

    async def mute_mentions(
        self, channel: Channel, *, duration: timedelta = None
    ) -> None:
        """Mute mentions in a channel

        Args:
            channel: Channel to mute mentions in
            duration: Duration of time to mute mentions
        """

    async def unmute_mentions(self, channel: Channel) -> None:
        """Unmute mentions in a channel

        Args:
            channel: Channel to unmute mentions in
        """
