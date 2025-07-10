from typing import List
from storage.db import SessionLocal
from storage.models import UserProgram

class UserProgramRepository:
    def __init__(self):
        self._session = SessionLocal()

    def list_by_user(self, user_id: int) -> List[UserProgram]:
        return (
            self._session
            .query(UserProgram)
            .filter(UserProgram.user_id == user_id)
            .all()
        )

    def get(self, user_program_id: int) -> UserProgram | None:
        return (
            self._session
            .query(UserProgram)
            .filter(UserProgram.user_program_id == user_program_id)
            .one_or_none()
        )

    def close(self):
        self._session.close()
