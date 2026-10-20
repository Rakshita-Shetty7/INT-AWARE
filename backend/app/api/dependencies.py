"""
FastAPI Dependency Injections.
"""

from backend.app.services.persistence_service import PersistenceService

_persistence_instance = PersistenceService()


def get_persistence_service() -> PersistenceService:
    """
    Dependency returning the shared PersistenceService.
    """
    return _persistence_instance
