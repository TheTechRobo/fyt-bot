import discord, aiohttp, asyncio

import urllib.parse as urllib # don't ask

from config import TOKEN

bot = discord.Bot()

@bot.event
async def on_ready():
    global session
    session = aiohttp.ClientSession()
    print(f"We have logged in as {bot.user}")

async def edit(message, content, embeds=[], **kwargs):
    return await message.edit_original_response(content=content, embeds=embeds, **kwargs)

@bot.slash_command()
async def search(ctx, id: str):
    """
    Searches findyoutubevideo.thetechrobo.ca for a YouTube video
    """
    try:
        message = await ctx.respond(f"Coercing to a video ID...")
        async with session.get("https://findyoutubevideo.thetechrobo.ca/api/coerce_to_id", params={"d": id}) as resp:
            if resp.status != 200:
                if resp.status == 400:
                    await edit(message, f"That doesn't look like a valid video ID or URL to me.\n(Server returned {await resp.text()})\nYou said: {id}")
                    return
                await edit(message, f"Server returned bad status code {resp.status} on API call.")
                return
            ident = (await resp.json())['data']
            await edit(message, f"Converted URL to {ident}.")
            await asyncio.sleep(1)
        await edit(message, f"Making request...")
        async with session.get(f"https://findyoutubevideo.thetechrobo.ca/api/v3/{ident}") as resp:
            data = await resp.json()
            verdict = data['verdict']['human_friendly'].replace("Video ", "")
            if data['verdict']['video']:
                colour = discord.Colour.green()
            elif data['verdict']['metaonly']:
                colour = discord.Colour.yellow()
            else:
                colour = discord.Colour.red()
            embed = discord.Embed(
                    title=f"Results for {ident}",
                    description=f"This video is {verdict}",
                    color=colour,
            )
            buttons = []
            buttons.append(discord.ui.Button(style=discord.ButtonStyle.link, url="https://findyoutubevideo.thetechrobo.ca/?q="+ident, label="View on findyoutubevideo.thetechrobo.ca", row=1))
            for key in data['keys']:
                archived = "Archived!" if key['archived'] else "Not archived"
                if key['metaonly'] and key['archived']:
                    archived += " (metadata only)"
                if key['comments']:
                    archived += " (including comments)"
                if key['error']:
                    archived = "Unknown"
                if key['name'] == "#youtubearchive": # Ugly hack
                    key['note'] = key['note'].replace("<a href='https://wiki.archiveteam.org/index.php/Archiveteam:IRC#How_do_I_chat_on_IRC?'>", "")
                    key['note'] = key['note'].replace("</a>", "")
                available = "" if not key['available'] else " A link is available below this message."
                if available:
                    buttons.append(discord.ui.Button(style=discord.ButtonStyle.link, url=key['available'], label=f"Visit {key['name']}", row=2))
                current_key = f"_{archived}_{available}\n{key['note'] if key['note'] else ''}"
                embed.add_field(name=key['name'], value=current_key, inline=True)
            embed.set_footer(text="Click 'View on findyoutubevideo.thetechrobo.ca' for more info!")
            view = discord.ui.View(*buttons, timeout=None)
            await edit(message, "See more details at https://findyoutubevideo.thetechrobo.ca/?q="+ident, embeds=[embed], view=view)
    except Exception as ename:
        await message.edit_original_response(content=f"An exception was raised!\nType: {type(ename)}\nData: {ename}", embeds=[])
        raise

@bot.event
async def on_error(ctx, error):
    print(ctx.msg)

bot.run(TOKEN)

