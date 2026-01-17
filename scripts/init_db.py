"""
Initialize database schema
"""

from packages.storage.database import engine, Base
from packages.storage.models import PromptModel, FamilyModel, LineageModel, ProcessingLogModel


def init_db():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


if __name__ == "__main__":
    init_db()
