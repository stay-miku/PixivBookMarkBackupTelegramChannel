from .Session import start_session, Bot, Illust, Channel, Backup, PreviewBackup, start_async_session, database_path
import asyncio


async def verify():
    process = await asyncio.create_subprocess_shell(f"sqlite3 {database_path}data.db 'insert into test default values'"
                                                    , stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                                                    , shell=True)
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        return False
    else:
        return True
