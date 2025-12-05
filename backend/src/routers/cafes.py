from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser, ManagerUser
from ..database import get_db
from ..schemas.cafe import CafeCreate, CafeResponse, CafeStatusUpdate, CafeUpdate
from ..services.cafe import CafeService

router = APIRouter(prefix="/cafes", tags=["cafes"])


def get_cafe_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CafeService:
    return CafeService(db)


@router.get("", response_model=list[CafeResponse])
async def list_cafes(
    current_user: CurrentUser,
    service: Annotated[CafeService, Depends(get_cafe_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
):
    """List all cafes."""
    # Non-managers only see active cafes
    if current_user.role != "manager":
        active_only = True
    return await service.list_cafes(skip=skip, limit=limit, active_only=active_only)


@router.post("", response_model=CafeResponse, status_code=201)
async def create_cafe(
    data: CafeCreate,
    manager: ManagerUser,
    service: Annotated[CafeService, Depends(get_cafe_service)],
):
    """Create a new cafe (manager only)."""
    return await service.create_cafe(data)


@router.get("/{cafe_id}", response_model=CafeResponse)
async def get_cafe(
    cafe_id: int,
    current_user: CurrentUser,
    service: Annotated[CafeService, Depends(get_cafe_service)],
):
    """Get cafe by ID."""
    return await service.get_cafe(cafe_id)


@router.patch("/{cafe_id}", response_model=CafeResponse)
async def update_cafe(
    cafe_id: int,
    data: CafeUpdate,
    manager: ManagerUser,
    service: Annotated[CafeService, Depends(get_cafe_service)],
):
    """Update cafe (manager only)."""
    return await service.update_cafe(cafe_id, data)


@router.delete("/{cafe_id}", status_code=204)
async def delete_cafe(
    cafe_id: int,
    manager: ManagerUser,
    service: Annotated[CafeService, Depends(get_cafe_service)],
):
    """Delete cafe (manager only)."""
    await service.delete_cafe(cafe_id)


@router.patch("/{cafe_id}/status", response_model=CafeResponse)
async def update_cafe_status(
    cafe_id: int,
    data: CafeStatusUpdate,
    manager: ManagerUser,
    service: Annotated[CafeService, Depends(get_cafe_service)],
):
    """Set cafe active status (manager only)."""
    return await service.update_status(cafe_id, data.is_active)
