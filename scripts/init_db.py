"""
Initialize database schema
"""

from packages.storage.database import engine, Base
# Import models to ensure they are registered with Base
from packages.storage.models import PromptInstance, PromptFamily, Template  # noqa: F401


def init_db():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")
    print("   Tables created: prompt_instances, prompt_families, templates")


if __name__ == "__main__":
    init_db()
