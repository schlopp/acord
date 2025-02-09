from __future__ import annotations

import pydantic
import datetime

from acord.bases import Hashable, Embed
from acord.core.abc import Route
from acord.models import User, Emoji, Sticker, Snowflake
from acord.errors import APIObjectDepreciated

from typing import Any, List, Optional, Union


async def _clean_reaction(string):
    if isinstance(string, str):
        string = string[0]
        # UNICODE chars are only 1 character long
        if string.isascii():
            raise ValueError("Incorrect unicode emoji provided")
    elif isinstance(string, Emoji):
        string = str(string)
    else:
        raise ValueError("Unknown emoji")

    return string


class MessageReference(pydantic.BaseModel):
    message_id: Snowflake
    channel_id: Optional[Snowflake]
    guild_id: Optional[Snowflake]
    fail_if_not_exists: Optional[bool] = True


class Message(pydantic.BaseModel, Hashable):
    conn: Any
    # Connection Object - For internal use

    activity: Any
    """ sent with Rich Presence-related chat embeds """  # TODO: Message Activity
    application: Any
    """ sent with Rich Presence-related chat embeds """  # TODO: Application Object
    attachments: List[Any]
    """ List of file objects """  # TODO: Asset object
    author: User
    """ User object of who sent the message """
    channel_id: int
    """ id of the channel were the message was send """
    components: List[Any]
    """ List of all components in the message """
    content: str
    """ Message content """

    edited_timestamp: Optional[
        Union[
            bool, datetime.datetime
        ]  # If not false contains timestamp of edited message
    ]
    embeds: List[Embed]
    """ List of embeds """
    flags: int
    """ Message flags """
    id: Snowflake
    """ Message ID """
    interaction: Optional[Any]
    """ Message Interaction """  # TODO: Interaction object
    guild_id: Optional[int]
    """ Guild ID of were message was sent """
    member: Optional[Any]
    """ Member object of who sent the message """  # TODO: Member object
    mentions: List[Union[User, Any]]
    """ List of mentioned users """
    mention_everyone: bool
    """ If message mentioned @everyone """
    mention_roles: List[Any]
    """ If message mentioned any roles """
    mention_channels: Optional[List[Any]]
    """ List of mentioned channels """  # TODO: Channel Object
    nonce: Optional[int]
    """ Message nonce: used for verifying if message was sent """
    pinned: bool
    """ Message pinned in channel or not """
    reactions: Optional[List[Any]] = list()
    """ List of reactions """  # TODO: reaction object
    referenced_message: Optional[Union[Message, MessageReference]]
    """ Replied message """  # TODO: partial message
    thread: Optional[Any]
    """ Thread were message was sent """  # TODO: Channel Thread Object
    timestamp: datetime.datetime
    """ List of reactions """ # TODO: reaction object
    referenced_message: Optional[
        Union[Message, MessageReference]  
    ]
    """ Replied message """
    thread: Optional[Any]  
    """ Thread were message was sent """ # TODO: Channel Thread Object
    timestamp: datetime.datetime  
    """ Timestamp of when message was sent """
    tts: bool
    """ Is a text to speech message """
    type: int
    """ Message type, e.g. DEFAULT, REPLY """
    sticker_items: Optional[List[Sticker]]
    """ List of stickers """
    stickers: Optional[List[Any]]
    # Depreciated raises error if provided
    webhook_id: Optional[int]
    """ Webhook message ID """

    class Config:
        arbitrary_types_allowed = True

    @pydantic.validator("timestamp")
    def _timestamp_validator(cls, timestamp):
        # :meta private:
        try:
            return datetime.datetime.fromisoformat(timestamp)
        except TypeError:
            if isinstance(timestamp, datetime.datetime):
                return timestamp
            raise

    @pydantic.validator("stickers")
    def _stickers_depr_error(cls, _):
        # :meta private:
        raise APIObjectDepreciated(
            '"stickers" attribute has been dropped, please use "sticker_items"'
        )

    @pydantic.validator("author")
    def _validate_author(cls, data: User, **kwargs):
        # :meta private:
        data = data.dict()
        conn = kwargs["values"]["conn"]

        data["conn"] = conn

        return User(**data)

    async def _get_bucket(self):
        return dict(channel_id=self.channel_id, guild_id=self.guild_id)

    async def refetch(self) -> Optional[Message]:
        """|coro|
        
        Attempts to fetch the same message from the API again"""
        return await self.conn.client.fetch_message(self.channel_id, self.id)

    @pydantic.validate_arguments
    async def get_reactions(self,
        emoji: Union[str, Emoji],
        *, 
        update: bool = True,
        after: Union[User, Snowflake],
        limit: int = 25
    ) -> List[User]:
        """|coro|
        
        Fetches users from a reaction

        Parameters
        ----------
        emoji: Union[:class:`str`, :class:`Emoji`]
            Emoji to fetch reactions for
        update: :class:`bool`
            Whether to update message object, defaults to ``True``
        after: Union[:class:`Snowflake`, :class:`User`]
            Fetches users after this id
        limit: :class:`int`
            Amount of users to fetch,
            any integer from 1 - 100
        """
        assert 1 <= limit <= 100, "Limit must be between 1 and 100"
        res = await self.conn.request(
            Route(
                "GET", 
                path=f"/channels/{self.channel_id}/messages/{self.id}/reactions/{emoji}",
                after=getattr(after, 'id', after),
                limit=limit,
                bucket=(await self._get_bucket())
            ))
        data = await res.json()
        users = list(map(lambda x: User(x), data))
        
        if update:
            pass

        return users

    async def delete(self, *, reason: str = None) -> None:
        """
        Deletes the message from the channel.
        Raises 403 is you don't have sufficient permissions or 404 is the message no longer exists.

        Parameters
        ----------
        reason: :class:`str`
            Reason for deleting message, shows up in AUDIT-LOGS
        """
        await self.conn.request(
            Route("DELETE", path=f"/channels/{self.channel_id}/messages/{self.id}"),
            headers={
                "X-Audit-Log-Reason": reason,
            },
            bucket=(await self._get_bucket()),
        )

    async def pin(self, *, reason: str = "") -> None:
        """ Adds message to channel pins """
        channel = self.channel

        if self.pinned:
            raise ValueError('This message has already been pinned')
            
        await self.conn.request(
            Route("PUT", path=f"/channels/{channel.id}/pins/{self.id}", bucket=(await self._get_bucket())),
            headers={'X-Audit-Log-Reason': str(reason)}
        )
        self.pinned = True

    async def unpin(self, *, reason: str = "") -> None:
        """ Removes message from channel pins """
        channel = self.channel

        if not self.pinned:
            raise ValueError('This message has not been pinned')

        await self.conn.request(
            Route(
                "DELETE", 
                path=f"/channels/{channel.id}/pins/{self.id}", 
                bucket=(await self._get_bucket())
            ),
            headers={'X-Audit-Log-Reason': str(reason)}
        )
        self.pinned = False

    async def add_reaction(self, emoji: Union[str, Emoji]) -> None:
        """
        Add an emoji to the message.
        Raises 403 if you lack permissions or 404 if message not found.

        Parameters
        ----------
        emoji: Union[:class:`str`, :class:`Emoji`]
            The emoji to add, if already on message does nothing
        """
        emoji = await _clean_reaction(emoji)

        # if self.has_reacted(self.conn.client):
        #     return

        await self.conn.request(
            Route(
                "PUT",
                path=f"/channels/{self.channel_id}/messages/{self.id}/reactions/{emoji}/@me",
                bucket={"channel_id": self.channel_id, "guild_id": self.guild_id},
            ),
        )

    async def remove_reaction(
        self, emoji: Union[str, Emoji], user_id: Union[str, int] = "@me"
    ) -> None:
        """
        Removes a reaction on a message set by a specified user.
        Raises 403 if you lack permissions or 404 if message not found.

        Parameters
        ----------
        emoji: Union[:class:`str`, :class:`Emoji`]
            Reaction to remove
        """
        emoji = await _clean_reaction(emoji)

        await self.conn.request(
            Route(
                "DELETE",
                path=f"/channels/{self.channel_id}/messages/{self.id}/reactions/{emoji}/{user_id}",
                bucket={"channel_id": self.channel_id, "guild_id": self.guild_id},
            ),
        )

    async def clear_reactions(self, *, emoji: Union[str, Emoji] = None) -> None:
        """
        Clear all reactions/x reactions on a message.
        Raises 403 if you lack permissions or 404 if message not found.

        Parameters
        ----------
        emoji: Union[:class:`str`, :class:`Emoji`]
            Emoji to clear, defaults to None meaning all
        """
        if emoji:
            emoji = await _clean_reaction(emoji)
            extension = f"/{emoji}"
        else:
            extension = ""

        await self.conn.request(
            Route(
                "DELETE",
                path=f"/channels/{self.channel_id}/messages/{self.id}/reactions{extension}",
                bucket={"channel_id": self.channel_id, "guild_id": self.guild_id},
            ),
        )

    async def reply(self, **data) -> Message:
        """Shortcut for `Message.Channel.send(..., reference=self)`"""
        data.update(message_reference=self)     # If provided gets overwritten

        return await self.channel.send(**data)

    async def crosspost(self) -> Message:
        channel = self.conn.client.get_channel(self.channel_id)

        if not channel:
            raise ValueError('Target channel no longer exists')
        resp = await self.conn.request(
            Route("POST", path=f"/channels/{channel.id}/messages/{self.id}/crosspost")
        )
        message =  Message(**(await resp.json()))
        self.conn.client.INTERNAL_STORAGE['messages'].update(
            {f'{message.channel_id}:{message.id}': message}
        )
        return message

    @property
    def channel(self):
        """ Returns the channel message was sent in """
        channel = self.conn.client.get_channel(self.channel_id)

        if not channel:
            raise ValueError('Target channel no longer exists')
        return channel
