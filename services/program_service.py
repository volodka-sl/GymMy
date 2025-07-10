from storage.user_repository import UserRepository
from storage.user_program_repository import UserProgramRepository
from storage.models import UserProgram

class ProgramService:
    def __init__(self, telegram_id: int):
        self._user_repo = UserRepository()
        self._program_repo = UserProgramRepository()
        self._user = self._user_repo.get_by_telegram_id(telegram_id)

    def list_user_programs(self) -> list[UserProgram]:
        if not self._user:
            return []
        return self._program_repo.list_by_user(self._user.user_id)
