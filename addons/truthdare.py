# Light UserBot
# Copyright (C) 2021-2022 CodeWithTyagi
#
# This file is a part of < https://github.com/CodeWithTyagi/Light >
# Please read the GNU Affero General Public License in
# https://www.github.com/CodeWithTyagi/Light/blob/main/LICENSE

"""
✘ Commands Available -

• `{i}truth`
   `Get Truth Task.`

• `{i}dare`
   `Get Dare Task.`
"""

import requests as r
from bs4 import BeautifulSoup as bs

from . import *

link = "https://fungenerators.com/random/truth-or-dare?option="


@light_cmd(pattern="truth$")
async def gtruth(ult):
    m = await ult.eor("`Generating a Truth Statement.. `")
    nl = link + "truth"
    ct = r.get(nl).content
    bsc = bs(ct, "html.parser", from_encoding="utf-8")
    cm = bsc.find_all("h2")[0].text
    await m.edit(f"**#TruthTask**\n\n`{cm}`")


@light_cmd(pattern="dare$")
async def gtruth(ult):
    m = await ult.eor("`Generating a Dare Task.. `")
    nl = link + "dare"
    ct = r.get(nl).content
    bsc = bs(ct, "html.parser", from_encoding="utf-8")
    cm = bsc.find_all("h2")[0].text
    await m.edit(f"**#DareTask**\n\n`{cm}`")
