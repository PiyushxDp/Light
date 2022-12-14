# Light UserBot
# Copyright (C) 2021-2022 CodeWithTyagi
#
# This file is a part of < https://github.com/CodeWithTyagi/Light >
# Please read the GNU Affero General Public License in
# https://www.github.com/CodeWithTyagi/Light/blob/main/LICENSE

import asyncio
import os
import shutil
import random
import time
from random import randint

try:
    from pytz import timezone
except ImportError:
    timezone = None

from telethon.errors import (
    ChannelsTooMuchError,
    ChatAdminRequiredError,
    MessageIdInvalidError,
    MessageNotModifiedError,
    UserNotParticipantError,
)
from telethon.tl.custom import Button
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditAdminRequest,
    EditPhotoRequest,
    InviteToChannelRequest,
)
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.types import (
    ChatAdminRights,
    ChatPhotoEmpty,
    InputChatUploadedPhoto,
    InputMessagesFilterDocument,
)
from telethon.utils import get_peer_id

from .. import LOGS, LightConfig
from ..fns.helper import download_file, inline_mention, updater


def update_envs():
    """Update Var. attributes to udB"""
    from .. import udB

    for envs in list(os.environ):
        if envs in ["LOG_CHANNEL", "BOT_TOKEN"] or envs in udB.keys():
            udB.set_key(envs, os.environ[envs])


async def startup_stuff():
    from .. import udB

    x = ["resources/auth", "resources/downloads"]
    for x in x:
        os.makedirs(x, exist_ok=True)

    CT = udB.get_key("CUSTOM_THUMBNAIL")
    if CT:
        path = "resources/extras/thumbnail.jpg"
        LightConfig.thumb = path
        try:
            await download_file(CT, path)
        except Exception as er:
            LOGS.exception(er)
    elif CT is False:
        LightConfig.thumb = None
    GT = udB.get_key("GDRIVE_AUTH_TOKEN")
    if GT:
        with open("resources/auth/gdrive_creds.json", "w") as t_file:
            t_file.write(GT)

    if udB.get_key("AUTH_TOKEN"):
        udB.del_key("AUTH_TOKEN")

    TZ = udB.get_key("TIMEZONE")
    if TZ and timezone:
        try:
            timezone(TZ)
            os.environ["TZ"] = TZ
            time.tzset()
        except AttributeError as er:
            LOGS.debug(er)
        except BaseException:
            LOGS.critical(
                "Incorrect Timezone ,\nCheck Available Timezone From Here https://graph.org/light-06-18-2\nSo Time is Default UTC"
            )
            os.environ["TZ"] = "UTC"
            time.tzset()


async def autobot():
    from .. import udB, light_bot

    if udB.get_key("BOT_TOKEN"):
        return
    await light_bot.start()
    LOGS.info("MAKING A TELEGRAM BOT FOR YOU AT @BotFather, Kindly Wait")
    who = light_bot.me
    name = who.first_name + "'s Bot"
    if who.username:
        username = who.username + "_bot"
    else:
        username = "light_" + (str(who.id))[5:] + "_bot"
    bf = "@BotFather"
    await light_bot(UnblockRequest(bf))
    await light_bot.send_message(bf, "/cancel")
    await asyncio.sleep(1)
    await light_bot.send_message(bf, "/newbot")
    await asyncio.sleep(1)
    isdone = (await light_bot.get_messages(bf, limit=1))[0].text
    if isdone.startswith("That I cannot do.") or "20 bots" in isdone:
        LOGS.critical(
            "Please make a Bot from @BotFather and add it's token in BOT_TOKEN, as an env var and restart me."
        )
        import sys

        sys.exit(1)
    await light_bot.send_message(bf, name)
    await asyncio.sleep(1)
    isdone = (await light_bot.get_messages(bf, limit=1))[0].text
    if not isdone.startswith("Good."):
        await light_bot.send_message(bf, "My Assistant Bot")
        await asyncio.sleep(1)
        isdone = (await light_bot.get_messages(bf, limit=1))[0].text
        if not isdone.startswith("Good."):
            LOGS.critical(
                "Please make a Bot from @BotFather and add it's token in BOT_TOKEN, as an env var and restart me."
            )
            import sys

            sys.exit(1)
    await light_bot.send_message(bf, username)
    await asyncio.sleep(1)
    isdone = (await light_bot.get_messages(bf, limit=1))[0].text
    await light_bot.send_read_acknowledge("botfather")
    if isdone.startswith("Sorry,"):
        ran = randint(1, 100)
        username = "light_" + (str(who.id))[6:] + str(ran) + "_bot"
        await light_bot.send_message(bf, username)
        await asyncio.sleep(1)
        isdone = (await light_bot.get_messages(bf, limit=1))[0].text
    if isdone.startswith("Done!"):
        token = isdone.split("`")[1]
        udB.set_key("BOT_TOKEN", token)
        await enable_inline(light_bot, username)
        LOGS.info(
            f"Done. Successfully created @{username} to be used as your assistant bot!"
        )
    else:
        LOGS.info(
            "Please Delete Some Of your Telegram bots at @Botfather or Set Var BOT_TOKEN with token of a bot"
        )

        import sys

        sys.exit(1)


async def autopilot():
    from .. import asst, udB, light_bot

    channel = udB.get_key("LOG_CHANNEL")
    new_channel = None
    if channel:
        try:
            chat = await light_bot.get_entity(channel)
        except BaseException as err:
            LOGS.exception(err)
            udB.del_key("LOG_CHANNEL")
            channel = None
    if not channel:

        async def _save(exc):
            udB._cache["LOG_CHANNEL"] = light_bot.me.id
            await asst.send_message(
                light_bot.me.id, f"Failed to Create Log Channel due to {exc}.."
            )

        if light_bot._bot:
            msg_ = "'LOG_CHANNEL' not found! Add it in order to use 'BOTMODE'"
            LOGS.error(msg_)
            return await _save(msg_)
        LOGS.info("Creating a Log Channel for You!")
        try:
            r = await light_bot(
                CreateChannelRequest(
                    title="My light Logs",
                    about="My light Log Group\n\n Join @CodeByTyagi",
                    megagroup=True,
                ),
            )
        except ChannelsTooMuchError as er:
            LOGS.critical(
                "You Are in Too Many Channels & Groups , Leave some And Restart The Bot"
            )
            return await _save(str(er))
        except BaseException as er:
            LOGS.exception(er)
            LOGS.info(
                "Something Went Wrong , Create A Group and set its id on config var LOG_CHANNEL."
            )

            return await _save(str(er))
        new_channel = True
        chat = r.chats[0]
        channel = get_peer_id(chat)
        udB.set_key("LOG_CHANNEL", str(channel))
    assistant = True
    try:
        await light_bot.get_permissions(int(channel), asst.me.username)
    except UserNotParticipantError:
        try:
            await light_bot(InviteToChannelRequest(int(channel), [asst.me.username]))
        except BaseException as er:
            LOGS.info("Error while Adding Assistant to Log Channel")
            LOGS.exception(er)
            assistant = False
    except BaseException as er:
        assistant = False
        LOGS.exception(er)
    if assistant and new_channel:
        try:
            achat = await asst.get_entity(int(channel))
        except BaseException as er:
            achat = None
            LOGS.info("Error while getting Log channel from Assistant")
            LOGS.exception(er)
        if achat and not achat.admin_rights:
            rights = ChatAdminRights(
                add_admins=True,
                invite_users=True,
                change_info=True,
                ban_users=True,
                delete_messages=True,
                pin_messages=True,
                anonymous=False,
                manage_call=True,
            )
            try:
                await light_bot(
                    EditAdminRequest(
                        int(channel), asst.me.username, rights, "Assistant"
                    )
                )
            except ChatAdminRequiredError:
                LOGS.info(
                    "Failed to promote 'Assistant Bot' in 'Log Channel' due to 'Admin Privileges'"
                )
            except BaseException as er:
                LOGS.info("Error while promoting assistant in Log Channel..")
                LOGS.exception(er)
    if isinstance(chat.photo, ChatPhotoEmpty):
        photo = await download_file(
            "https://graph.org/file/27c6812becf6f376cbb10.jpg", "channelphoto.jpg"
        )
        ll = await light_bot.upload_file(photo)
        try:
            await light_bot(EditPhotoRequest(int(channel), InputChatUploadedPhoto(ll)))
        except BaseException as er:
            LOGS.exception(er)
        os.remove(photo)


# customize assistant
async def customize():
    from .. import asst, udB, light_bot

    rem = None
    try:
        chat_id = udB.get_key("LOG_CHANNEL")
        if asst.me.photo:
            return
        LOGS.info("Customising Ur Assistant Bot in @BOTFATHER")
        UL = f"@{asst.me.username}"
        if not light_bot.me.username:
            sir = light_bot.me.first_name
        else:
            sir = f"@{light_bot.me.username}"
        file = random.choice(
            [
                "https://graph.org/file/4891739d286e78897ea8c.jpg",
                "https://graph.org/file/4891739d286e78897ea8c.jpg",
                "resources/extras/light_assistant.jpg",
            ]
        )
        if not os.path.exists(file):
            file = await download_file(file, "profile.jpg")
            rem = True
        msg = await asst.send_message(
            chat_id, "**Auto Customisation** Started on @Botfather"
        )
        await asyncio.sleep(1)
        await light_bot.send_message("botfather", "/cancel")
        await asyncio.sleep(1)
        await light_bot.send_message("botfather", "/setuserpic")
        await asyncio.sleep(1)
        isdone = (await light_bot.get_messages("botfather", limit=1))[0].text
        if isdone.startswith("Invalid bot"):
            LOGS.info("Error while trying to customise assistant, skipping...")
            return
        await light_bot.send_message("botfather", UL)
        await asyncio.sleep(1)
        await light_bot.send_file("botfather", file)
        await asyncio.sleep(2)
        await light_bot.send_message("botfather", "/setabouttext")
        await asyncio.sleep(1)
        await light_bot.send_message("botfather", UL)
        await asyncio.sleep(1)
        await light_bot.send_message(
            "botfather", f"✨ Hello ✨!! I'm Assistant Bot of {sir}"
        )
        await asyncio.sleep(2)
        await light_bot.send_message("botfather", "/setdescription")
        await asyncio.sleep(1)
        await light_bot.send_message("botfather", UL)
        await asyncio.sleep(1)
        await light_bot.send_message(
            "botfather",
            f"✨ Powerful light Assistant Bot ✨\n✨ Master ~ {sir} ✨\n\n✨ Powered By ~ @CodeByTyagi ✨",
        )
        await asyncio.sleep(2)
        await msg.edit("Completed **Auto Customisation** at @BotFather.")
        if rem:
            os.remove(file)
        LOGS.info("Customisation Done")
    except Exception as e:
        LOGS.exception(e)


async def plug(plugin_channels):
    from .. import light_bot
    from .utils import load_addons

    if light_bot._bot:
        LOGS.info("Plugin Channels can't be used in 'BOTMODE'")
        return
    os.makedirs("addons", exist_ok=True)
    if not os.path.isfile("addons/__init__.py"):
        with open("addons/__init__.py", "w") as f:
            f.write("from plugins import *\n\nbot = light_bot")
    LOGS.info("• Loading Plugins from Plugin Channel(s) •")
    for chat in plugin_channels:
        LOGS.info(f"{'•'*4} {chat}")
        try:
            async for x in light_bot.iter_messages(
                chat, search=".py", filter=InputMessagesFilterDocument, wait_time=10
            ):
                plugin = "addons/" + x.file.name.replace("_", "-").replace("|", "-")
                if not os.path.exists(plugin):
                    await asyncio.sleep(0.6)
                    if x.text == "#IGNORE":
                        continue
                    plugin = await x.download_media(plugin)
                try:
                    load_addons(plugin)
                except Exception as e:
                    LOGS.info(f"LightBot - PLUGIN_CHANNEL - ERROR - {plugin}")
                    LOGS.exception(e)
                    os.remove(plugin)
        except Exception as er:
            LOGS.exception(er)


# some stuffs


async def ready():
    from .. import asst, udB, light_bot
    from ..fns.tools import async_searcher

    chat_id = udB.get_key("LOG_CHANNEL")
    spam_sent = None
    if not udB.get_key("INIT_DEPLOY"):  # Detailed Message at Initial Deploy
        MSG = """🎇 **Thanks for Deploying Light Userbot!**
• Here, are the Some Basic stuff from, where you can Know, about its Usage."""
        PHOTO = "https://graph.org/file/838c45c9cc32dd131a621.jpg"
        BTTS = Button.inline("• Click to Start •", "initft_2")
        udB.set_key("INIT_DEPLOY", "Done")
    else:
        MSG = f"**Light Bot has been deployed!**\n➖➖➖➖➖➖➖➖➖➖\n**UserMode**: {inline_mention(light_bot.me)}\n**Assistant**: @{asst.me.username}\n➖➖➖➖➖➖➖➖➖➖\n**Support**: @CodeWithTyagi\n➖➖➖➖➖➖➖➖➖➖"
        BTTS, PHOTO = None, None
        prev_spam = udB.get_key("LAST_UPDATE_LOG_SPAM")
        if prev_spam:
            try:
                await light_bot.delete_messages(chat_id, int(prev_spam))
            except Exception as E:
                LOGS.info("Error while Deleting Previous Update Message :" + str(E))
        if await updater():
            BTTS = Button.inline("Update Available", "updtavail")

    try:
        spam_sent = await asst.send_message(chat_id, MSG, file=PHOTO, buttons=BTTS)
    except ValueError as e:
        try:
            await (await light_bot.send_message(chat_id, str(e))).delete()
            spam_sent = await asst.send_message(chat_id, MSG, file=PHOTO, buttons=BTTS)
        except Exception as g:
            LOGS.info(g)
    except Exception as el:
        LOGS.info(el)
        try:
            spam_sent = await light_bot.send_message(chat_id, MSG)
        except Exception as ef:
            LOGS.info(ef)
    if spam_sent and not spam_sent.media:
        udB.set_key("LAST_UPDATE_LOG_SPAM", spam_sent.id)


async def WasItRestart(udb):
    key = udb.get_key("_RESTART")
    if not key:
        return
    from .. import asst, light_bot

    try:
        data = key.split("_")
        who = asst if data[0] == "bot" else light_bot
        await who.edit_message(
            int(data[1]), int(data[2]), "__Restarted Successfully.__"
        )
    except Exception as er:
        LOGS.exception(er)
    udb.del_key("_RESTART")


def _version_changes(udb):
    for _ in [
        "BOT_USERS",
        "BOT_BLS",
        "VC_SUDOS",
        "SUDOS",
        "CLEANCHAT",
        "LOGUSERS",
        "PLUGIN_CHANNEL",
        "CH_SOURCE",
        "CH_DESTINATION",
        "BROADCAST",
    ]:
        key = udb.get_key(_)
        if key and str(key)[0] != "[":
            key = udb.get(_)
            new_ = [
                int(z) if z.isdigit() or (z.startswith("-") and z[1:].isdigit()) else z
                for z in key.split()
            ]
            udb.set_key(_, new_)


async def enable_inline(light_bot, username):
    bf = "BotFather"
    await light_bot.send_message(bf, "/setinline")
    await asyncio.sleep(1)
    await light_bot.send_message(bf, f"@{username}")
    await asyncio.sleep(1)
    await light_bot.send_message(bf, "Search")
    await light_bot.send_read_acknowledge(bf)
