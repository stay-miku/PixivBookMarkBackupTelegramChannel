from pagermaid.listener import listener
from pagermaid.utils import alias_command
from pagermaid import bot
from pagermaid.enums import Message


bot_name = "pixivBookmarksBackupBot"


@listener(is_plugin=True, command=alias_command("sql"), description="执行sql语句,需要备份bot支持", parameters="<SQL>|sql语句")
async def ss(context: Message):
    async with bot.conversation(bot_name) as conversation:
        if context.parameter:
            await context.edit(f"sqlite> {context.arguments}")
            await conversation.send_message(f"/sql {context.arguments}")
        else:
            await context.edit("没有参数")
            return
        try:
            chat_response = await conversation.get_response()
        except Exception:
            return await context.edit("执行失败")
        await conversation.mark_as_read()
        await context.edit(chat_response.text)


@listener(is_plugin=True, command=alias_command("shell"), description="执行shell命令,需要备份bot支持", parameters="<COMMAND>|命令")
async def ss(context: Message):
    async with bot.conversation(bot_name) as conversation:
        if context.parameter:
            await context.edit(f"~# {context.arguments}")
            await conversation.send_message(f"/shell {context.arguments}")
        else:
            await context.edit("没有参数")
            return
        try:
            chat_response = await conversation.get_response()
        except Exception:
            return await context.edit("执行失败")
        await conversation.mark_as_read()
        await context.edit(chat_response.text)


