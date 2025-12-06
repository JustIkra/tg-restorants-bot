from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import ManagerUser
from ..database import get_db
from ..schemas.summary import SummaryCreate, SummaryResponse
from ..services.summary import SummaryService

router = APIRouter(prefix="/summaries", tags=["summaries"])


def get_summary_service(db: Annotated[AsyncSession, Depends(get_db)]) -> SummaryService:
    return SummaryService(db)


@router.get("", response_model=list[SummaryResponse])
async def list_summaries(
    manager: ManagerUser,
    service: Annotated[SummaryService, Depends(get_summary_service)],
    cafe_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List summaries (manager only)."""
    return await service.list_summaries(cafe_id=cafe_id, skip=skip, limit=limit)


@router.post("", response_model=SummaryResponse, status_code=201)
async def create_summary(
    data: SummaryCreate,
    manager: ManagerUser,
    service: Annotated[SummaryService, Depends(get_summary_service)],
):
    """Create a summary report (manager only)."""
    return await service.create_summary(data)


@router.get("/{summary_id}")
async def get_summary(
    summary_id: int,
    manager: ManagerUser,
    service: Annotated[SummaryService, Depends(get_summary_service)],
    format: str = Query("json", pattern=r"^(json|csv)$"),
):
    """Get summary by ID (manager only). Supports json and csv formats."""
    summary = await service.get_summary(summary_id)

    if format == "csv":
        csv_content = service.format_summary_csv(summary)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=summary_{summary_id}.csv"
            },
        )

    return SummaryResponse.model_validate(summary)


@router.delete("/{summary_id}", status_code=204)
async def delete_summary(
    summary_id: int,
    manager: ManagerUser,
    service: Annotated[SummaryService, Depends(get_summary_service)],
):
    """Delete summary (manager only)."""
    await service.delete_summary(summary_id)
