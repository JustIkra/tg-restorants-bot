from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.user import UserRepository
from ..schemas.user import BalanceResponse, UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        role: str | None = None,
    ):
        return await self.repo.list(skip=skip, limit=limit, search=search, role=role)

    async def get_user(self, tgid: int):
        user = await self.repo.get_by_tgid(tgid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def create_user(self, data: UserCreate, role: str = "user"):
        existing = await self.repo.get_by_tgid(data.tgid)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            )
        return await self.repo.create(
            tgid=data.tgid,
            name=data.name,
            office=data.office,
            role=role,
        )

    async def update_user(self, tgid: int, data: UserUpdate):
        user = await self.get_user(tgid)
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(user, **update_data)

    async def delete_user(self, tgid: int):
        user = await self.get_user(tgid)
        await self.repo.delete(user)

    async def update_access(self, tgid: int, is_active: bool):
        user = await self.get_user(tgid)
        return await self.repo.update(user, is_active=is_active)

    async def get_balance(self, tgid: int) -> BalanceResponse:
        user = await self.get_user(tgid)
        spent = await self.repo.get_spent_this_week(tgid)

        remaining = None
        if user.weekly_limit is not None:
            remaining = user.weekly_limit - spent

        return BalanceResponse(
            tgid=user.tgid,
            weekly_limit=user.weekly_limit,
            spent_this_week=spent,
            remaining=remaining,
        )

    async def update_balance_limit(self, tgid: int, weekly_limit: Decimal | None):
        user = await self.get_user(tgid)
        return await self.repo.update(user, weekly_limit=weekly_limit)
