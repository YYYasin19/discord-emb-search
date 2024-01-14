import discord
from discord import Message
from discord.ext.commands import Context
from discord.ext import commands
from discord.channel import TextChannel
from dotenv import load_dotenv
from discord_embed_bot.embedding import EmbeddingSearch, SearchResult
import os

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

emb_search = EmbeddingSearch()  # TODO: get on other server's as well?

command_list = ["!search", "!index"]


def _filter_embed(message: Message) -> bool:
    """
    returns whether the message should be embedded or not.
    True -> embed the message.
    """
    long_enough = len(message.content.strip()) > 20
    in_command_list = any([message.content.startswith(c) for c in command_list])
    from_bot = (message.author == bot.user) or (message.author.bot) or (message.author.system)
    return long_enough and (not in_command_list) and (not from_bot)


# TODO: remove this method or write the user directly or something like that.. create a new channel maybe?
@bot.event
async def on_ready():
    channel = bot.get_channel(1195726927659536516)
    if channel:
        await channel.send("Hi! Bin online.")  # type: ignore

        print(f"{bot.user} is connected to the following server:\n")
        for server in bot.guilds:
            print(f"{server.name}(id: {server.id})")


@bot.command(name="search")
async def search_commannd(ctx: Context, arg):
    print(f"log: search with {ctx} for [{ctx.message}]")
    try:
        message = ctx.message
        query_str = message.content.replace("!search", "").lstrip() or arg

        if guild := ctx.message.guild:
            search_result: list[SearchResult] = await emb_search.search(query_str, k=3, guild_id=guild.id)
            search_response = await emb_search.build_response(search_result)
            await message.channel.send(search_response)
    except Exception as e:
        print(e)


@bot.command(name="index")
async def index_command(ctx: Context, arg):
    """
    indexes all messages on a server
    """
    channel_limit = None
    try:
        channel_limit = int(arg)
    except Exception as e:
        print(e)

    await ctx.message.reply("Start indexing!")
    counter = 0
    storage = {"messages": [], "message_ids": [], "channel_ids": [], "guild_ids": []}
    if ctx.guild:
        for channel in ctx.guild.channels:
            await ctx.message.reply(f"🔍 through [{channel.name}]")
            if isinstance(channel, TextChannel):
                async for message in channel.history(limit=channel_limit):
                    counter += 1
                    if _filter_embed(message):
                        storage["messages"].append(message.content)
                        storage["message_ids"].append(message.id)
                        storage["channel_ids"].append(message.channel.id)
                        storage["guild_ids"].append(message.guild.id if message.guild else 0)

    stored_messages: int = await emb_search.batch_embed_messages(
        storage["messages"],
        storage["message_ids"],
        storage["channel_ids"],
        storage["guild_ids"],
        recreate=True,  # rebuild database
    )

    await ctx.channel.send(f"Went through {counter} messages and stored {stored_messages} of 'em.")


@bot.event
async def on_message(message: Message):
    if _filter_embed(message):
        await emb_search.embed_message(
            message.content,
            message.id,
            message.channel.id,
            message.guild.id if message.guild else 0,
        )
        # await message.add_reaction("✅")
    await bot.process_commands(message)


def main():
    # will run blocking, for non-blocking use bot.start()
    bot.run(os.environ.get("BOT_TOKEN", ""))


if __name__ == "__main__":
    main()
