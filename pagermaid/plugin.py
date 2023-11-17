from pagermaid.listener import listener
from pagermaid.utils import alias_command
from pagermaid import bot
from pagermaid.enums import Message


bot_name = "pixivBookmarksBackupBot"


@listener(is_plugin=True, command=alias_command("ss"), description="快捷发送涩图,需使用备份bot")
async def ss(context: Message):
    await context.edit("正在涩涩~")
    async with bot.conversation(bot_name) as conversation:
        await conversation.send_message("/rand")
        try:
            chat_response = await conversation.get_response()
        except Exception:
            return await context.edit("没有找到涩图!!")

        await bot.forward_messages(from_chat_id=conversation.chat_id, message_ids=chat_response.id, chat_id=context.chat_id)
        await context.delete()



