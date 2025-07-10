from aiogram import Bot

class BotNotifier:
    def __init__(self, token: str):
        self._token = token

    async def send(self, chat_id: int, text: str, parse_mode: str = None):
        """
        Отправляет сообщение пользователю.
        Не занимается никакой другой логикой.
        """
        bot = Bot(token=self._token)
        try:
            await bot.send_message(chat_id, text, parse_mode=parse_mode)
        finally:
            await bot.session.close()
