#!/usr/bin/env python3
import sys
import asyncio
import datetime
import logging
import logging.handlers
from FoxDedsDB.dedsdb import init_db
from FoxDedsDB.dedsdb import get_deds
from FoxDedsDB.dedsdb import add_ded
from FoxDedsDB.dedsdb import add_game
from FoxDedsDB.dedsdb import set_current
from Settings.settings import Settings

description = "A bot to track FociePlays Deds"

try:
    assert sys.version_info >= (3, 5)
    from discord.ext import commands
    import discord
except ImportError:
    print("Discord.py is not installed.\n"
          "Consult the guide for your operating system "
          "and do ALL the steps in order.\n")
    sys.exit()
except AssertionError:
    print("FocieDeds needs Python 3.5 or superior.\n"
          "Consult the guide for your operating system "
          "and do ALL the steps in order.\n")
    sys.exit()


class FocieDeds(commands.Bot):
    def __init__(self, *args, **kwargs):
        self._db = kwargs["db"]
        self.uptime = datetime.datetime.utcnow()
        self.settings = Settings()
        self.self_bot = False
        self._intro_displayed = False
        self.auto_restart = True
        self.last_added = None
        super().__init__(*args, **kwargs)


def send_deds():
    global conn
    c = conn.cursor()


def init(bot_class=FocieDeds):
    bot = bot_class(command_prefix='!', description=description, db="FociePlaysDeds.db")

    def check_roles(droles):
        roles = [n.name for n in droles]
        return set(roles).intersection(set(bot.settings.spec_roles))

    @bot.event
    @asyncio.coroutine
    def on_ready():
        if bot._intro_displayed:
            return
        bot._intro_displayed = True

        login_time = datetime.datetime.utcnow() - bot.uptime
        login_time = login_time.seconds + login_time.microseconds / 1E6

        print("Login successful. ({}ms)\n".format(login_time))
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('------')

        if bot.settings.token and not bot.settings.self_bot:
            print("\nUse this url to bring your bot to a server:")
            url = yield from get_oauth_url()
            bot.oauth_url = url
        print(url)

    @bot.event
    @asyncio.coroutine
    def on_message(message):
        if not message.author.bot:
            yield from bot.process_commands(message)

    @bot.command()
    @asyncio.coroutine
    def deds(game: str = ""):
        yield from bot.say(get_deds(bot._db, game))

    @bot.command(pass_context=True)
    @asyncio.coroutine
    def addded(ctx, game="", desc=""):
        if check_roles(ctx.message.author.roles):
            diff = 61
            now = datetime.datetime.now()
            if bot.last_added is not None:
                diff = (now - bot.last_added).total_seconds()
            if diff > 60:
                bot.last_added = now
                msg = add_ded(bot._db, game, desc)
            else:
                msg = f"Last ded added {diff} seconds ago. Too soon to add moar deds."
        else:
            msg = f"You are not part of {bot.settings.mod_role} and cannot add moar deds."
        yield from bot.say(msg)

    @bot.command(pass_context=True)
    @asyncio.coroutine
    def addgame(ctx, game: str):
        if check_roles(ctx.message.author.roles):
            msg = add_game(bot._db, game)
        else:
            msg = f"You are not part of {bot.settings.mod_role} and cannot add new games."
        yield from bot.say(msg)

    @bot.command(pass_context=True)
    @asyncio.coroutine
    def setgame(ctx, game: str):
        if check_roles(ctx.message.author.roles):
            msg = set_current(bot._db, game)
        else:
            msg = f"You are not part of {bot.settings.mod_role} and cannot set the current game."
        yield from bot.say(msg)

    @bot.command()
    @asyncio.coroutine
    def dedhelp(command=""):
        helps = {"basehelp":
                     ("FocieDedsBot supports the following commands:\n"
                      "**!deds** [gamename]\n"
                      "**!added** [gamename] [description]\n"
                      "**!addgame** gamename\n"
                      "**!setgame** gamename\n"
                      "Items marked with [] are optional.\n"
                      "Type \"**!dedhelp** commandname\" for details about a specific command.\n"
                      "Example: \"**!dedhelp** deds\" will provide help on **!deds**\n"

                      ),
                 "deds":
                     ("**!deds** [gamename]\n"
                      "Tells the channel how many deds.\n"
                      "If no gamename is provided, uses the game marked current as a default.\n"
                      ),
                 "addded":
                     ("**!addded** [gamename] [description]\n"
                      "**Requires user to have \"Deds\" role.**\n"
                      "Adds another ded to the counter for gamename, with an optional description.\n"
                      "If no gamename is provided, uses the game marked current as a default.\n"
                      "If no description is provided, \"No ded infos.\" is used as a default.\n"
                      ),
                 "addgame":
                     ("**!addgame** gamename\n"
                      "**Requires user to have \"Deds\" role.**\n"
                      "Sets up \"gamename\" as a game with deds tracking.\n"
                      ),
                 "setgame":
                     ("**!setgame** gamename\n"
                      "**Requires user to have \"Deds\" role.**\n"
                      "Marks \"gamename\" as the current game and default for **!deds** and **!addded**.\n"
                      ),
                 }
        if command is "":
            lkup = "basehelp"
        else:
            lkup = command
        yield from bot.say(helps[lkup])

    @asyncio.coroutine
    def get_oauth_url():
        try:
            data = yield from bot.application_info()
        except Exception as e:
            return "Couldn't retrieve invite link.Error: {}".format(e)
        return discord.utils.oauth_url(data.id)

    return bot


def main(bot):
    # if not bot.settings.no_prompt:
    # interactive_setup(bot.settings)
    # load_cogs(bot)

    # if bot.settings._dry_run:
    #    print("Quitting: dry run")
    #    bot._shutdown_mode = True
    #    exit(0)

    print("Logging into Discord...")
    bot.uptime = datetime.datetime.utcnow()

    if bot.settings.login_credentials:
        yield from bot.login(*bot.settings.login_credentials,
                             bot=not bot.settings.self_bot)
    else:
        print("No credentials available to login.")
        raise RuntimeError()
    yield from bot.connect()


if __name__ == '__main__':

    init_db("FociePlaysDeds.db")
    bot = init()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(bot))
    except discord.LoginFailure:
        print("Unable to log in to Discord. Try again later, or reset credentials and try again.")
    except KeyboardInterrupt:
        loop.run_until_complete(bot.logout())
    except Exception as e:
        bot.logger.exception("Fatal exception, attempting graceful logout",
                             exc_info=e)
        loop.run_until_complete(bot.logout())
    finally:
        loop.close()
        if bot.auto_restart:
            exit(26)
        elif bot.auto_restart is False:
            exit(0)
        else:
            exit(1)

