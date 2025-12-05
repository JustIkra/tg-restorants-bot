from .auth import router as auth_router
from .cafes import router as cafes_router
from .deadlines import router as deadlines_router
from .menu import router as menu_router
from .orders import router as orders_router
from .summaries import router as summaries_router
from .users import router as users_router

__all__ = [
    "auth_router",
    "users_router",
    "cafes_router",
    "menu_router",
    "deadlines_router",
    "orders_router",
    "summaries_router",
]
