from discord.ext import commands
import discord


class CommandHelp:
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='repeat', aliases=['mimic', 'copy'])
    async def command_help(self, ctx, *, inp: str):
        await ctx.send(inp)

def setup(bot):
    bot.add_cog(CommandHelp(bot))