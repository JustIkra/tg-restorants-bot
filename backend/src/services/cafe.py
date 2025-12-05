from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.cafe import CafeRepository
from ..schemas.cafe import CafeCreate, CafeUpdate


class CafeService:
    def __init__(self, session: AsyncSession):
        self.repo = CafeRepository(session)

    async def list_cafes(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ):
        return await self.repo.list(skip=skip, limit=limit, active_only=active_only)

    async def get_cafe(self, cafe_id: int):
        cafe = await self.repo.get(cafe_id)
        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cafe not found",
            )
        return cafe

    async def create_cafe(self, data: CafeCreate):
        return await self.repo.create(
            name=data.name,
            description=data.description,
        )

    async def update_cafe(self, cafe_id: int, data: CafeUpdate):
        cafe = await self.get_cafe(cafe_id)
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(cafe, **update_data)

    async def delete_cafe(self, cafe_id: int):
        cafe = await self.get_cafe(cafe_id)
        await self.repo.delete(cafe)

    async def update_status(self, cafe_id: int, is_active: bool):
        cafe = await self.get_cafe(cafe_id)
        return await self.repo.update(cafe, is_active=is_active)
