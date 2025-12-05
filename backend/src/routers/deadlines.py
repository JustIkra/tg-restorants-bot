from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import ManagerUser
from ..database import get_db
from ..schemas.deadline import DeadlineSchedule, DeadlineScheduleUpdate
from ..services.deadline import DeadlineService

router = APIRouter(tags=["deadlines"])


def get_deadline_service(db: Annotated[AsyncSession, Depends(get_db)]) -> DeadlineService:
    return DeadlineService(db)


@router.get("/cafes/{cafe_id}/deadlines", response_model=DeadlineSchedule)
async def get_deadlines(
    cafe_id: int,
    manager: ManagerUser,
    service: Annotated[DeadlineService, Depends(get_deadline_service)],
):
    """Get deadline schedule for a cafe (manager only)."""
    return await service.get_schedule(cafe_id)


@router.put("/cafes/{cafe_id}/deadlines", response_model=DeadlineSchedule)
async def update_deadlines(
    cafe_id: int,
    data: DeadlineScheduleUpdate,
    manager: ManagerUser,
    service: Annotated[DeadlineService, Depends(get_deadline_service)],
):
    """Update deadline schedule for a cafe (manager only)."""
    return await service.update_schedule(cafe_id, data)
