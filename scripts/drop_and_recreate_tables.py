"""Drop all tables and recreate with new schema.

This script completely drops all tables and recreates them based on the
current SQLAlchemy models. Use this when you've changed the model schema.

WARNING: This will delete ALL data!
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import engine
from app.models import Base


def drop_and_recreate_tables():
    """Drop all tables and recreate them with current schema."""
    print("=" * 70)
    print("DROP AND RECREATE TABLES")
    print("=" * 70)
    print("\nWARNING: This will delete ALL data in the database!")
    print("\nDropping all tables...")
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("✓ All tables dropped")
    
    # Recreate all tables with new schema
    print("\nRecreating all tables with current schema...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables recreated")
    
    print("\n" + "=" * 70)
    print("✓ Database schema updated successfully!")
    print("=" * 70)


if __name__ == "__main__":
    drop_and_recreate_tables()
