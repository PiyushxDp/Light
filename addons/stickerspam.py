# Light UserBot
# Copyright (C) 2021-2022 CodeWithTyagi
#
# This file is a part of < https://github.com/CodeWithTyagi/Light >
# Please read the GNU Affero General Public License in
# https://www.github.com/CodeWithTyagi/Light/blob/main/LICENSE

"""
✘ Commands Available -

•`{i}sspam <reply to sticker> <optional- time gap>`
   it spam the whole stickers in that pack.

"""

import asyncio

from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetID, InputStickerSetShortName
from telethon.utils import get_input_document

from . import *


@light_cmd(pattern="sspam ?(.*)")
async def _(e):
    match = e.pattern_match.group(1)
    x = await e.get_reply_message()
    if not (x and x.media and hasattr(x.media, "document")):
        return await eod(e, "`Reply To Sticker Only`")
    set = x.document.attributes[1]
    sset = await e.client(
        GetStickerSetRequest(
            InputStickerSetID(
                id=set.stickerset.id, access_hash=set.stickerset.access_hash
            ),
            hash=0,
        )
    )
    pack = sset.set.short_name
    docs = [
        get_input_document(x)
        for x in (
            await e.client(GetStickerSetRequest(InputStickerSetShortName(pack), hash=0))
        ).documents
    ]
    try:
        match = int(match)
    except ValueError:
        match = None
    for xx in docs:
        if match:
            await asyncio.sleep(match)
        await e.respond(file=xx)
