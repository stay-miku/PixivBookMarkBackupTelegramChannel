from pagermaid.listener import listener
from pagermaid.utils import alias_command
from pagermaid import bot
from pagermaid.enums import Message


bot_name = "pixivBookmarksBackupBot"


@listener(is_plugin=True, command=alias_command("ss"), description="快捷发送涩图,需使用备份bot", parameters="<tag>...|过滤作品的tag")
async def ss(context: Message):
    await context.edit("正在涩涩~")
    async with bot.conversation(bot_name) as conversation:
        if context.parameter:
            await conversation.send_message(f"/rand {context.arguments}")
        else:
            await conversation.send_message("/rand")
        try:
            chat_response = await conversation.get_response()
        except Exception:
            return await context.edit("没有找到涩图!!")
        await conversation.mark_as_read()
        await chat_response.copy(chat_id=context.chat.id)
        await context.safe_delete()


@listener(is_plugin=True, command=alias_command("search"), description="快捷搜索,需使用备份bot", parameters="<KEYWORD>...|过滤作品的关键词")
async def ss(context: Message):
    await context.edit("正在搜索~")
    async with bot.conversation(bot_name) as conversation:
        if context.parameter:
            await conversation.send_message(f"/search {context.arguments}")
        else:
            await context.edit("缺少参数")
            return
        try:
            chat_response = await conversation.get_response()
        except Exception:
            return await context.edit("没有找到涩图!!")
        await conversation.mark_as_read()
        await chat_response.copy(
            context.chat.id
        )
        await context.safe_delete()



