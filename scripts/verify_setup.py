"""
Verify that the project setup is correct
"""

import sys
from pathlib import Path

def check_imports():
    """Check if all package imports work"""
    errors = []
    
    try:
        from packages.core.models import PromptDNA, PromptFamily
        print("✅ Core models import successful")
    except ImportError as e:
        errors.append(f"❌ Core models: {e}")
    
    try:
        from packages.ingestion.files import ingest_from_file
        print("✅ Ingestion imports successful")
    except ImportError as e:
        errors.append(f"❌ Ingestion: {e}")
    
    try:
        from packages.dna_extractor.extractor import extract_dna
        print("✅ DNA extractor imports successful")
    except ImportError as e:
        errors.append(f"❌ DNA extractor: {e}")
    
    try:
        from packages.clustering.engine import cluster_prompts
        print("✅ Clustering imports successful")
    except ImportError as e:
        errors.append(f"❌ Clustering: {e}")
    
    try:
        from packages.storage.database import get_db
        print("✅ Storage imports successful")
    except ImportError as e:
        errors.append(f"❌ Storage: {e}")
    
    return errors


def check_structure():
    """Check if directory structure is correct"""
    required_dirs = [
        "apps/api",
        "apps/cli",
        "packages/core",
        "packages/ingestion",
        "packages/dna_extractor",
        "packages/clustering",
        "packages/llm",
        "packages/storage",
        "infra",
        "scripts",
    ]
    
    errors = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            errors.append(f"❌ Missing directory: {dir_path}")
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    return errors


def main():
    """Run all verification checks"""
    print("🔍 Verifying Evolv setup...\n")
    
    print("📁 Checking directory structure...")
    structure_errors = check_structure()
    print()
    
    print("📦 Checking package imports...")
    import_errors = check_imports()
    print()
    
    if structure_errors or import_errors:
        print("❌ Setup verification failed!")
        for error in structure_errors + import_errors:
            print(f"  {error}")
        print("\n💡 Try running: uv sync")
        sys.exit(1)
    else:
        print("✅ All checks passed! Setup is correct.")
        print("\n🚀 Next steps:")
        print("  1. Copy .env.example to .env and configure")
        print("  2. Run: uv run python scripts/init_db.py")
        print("  3. Run: uv run uvicorn apps.api.main:app --reload")


if __name__ == "__main__":
    main()
