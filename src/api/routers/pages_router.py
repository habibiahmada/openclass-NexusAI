"""
Pages Router
Serves HTML pages for different user roles
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

from ..config import config

router = APIRouter(tags=["pages"])


def create_pages_router():
    """Create pages router"""
    
    @router.get("/")
    async def root():
        """Serve landing page"""
        return FileResponse(config.frontend_dir / "index.html")
    
    @router.get("/siswa")
    async def siswa_page():
        """Serve student page"""
        return FileResponse(config.frontend_dir / "pages" / "siswa.html")
    
    @router.get("/guru")
    async def guru_page():
        """Serve teacher page"""
        return FileResponse(config.frontend_dir / "pages" / "guru.html")
    
    @router.get("/admin")
    async def admin_page():
        """Serve admin page"""
        return FileResponse(config.frontend_dir / "pages" / "admin.html")
    
    return router
