"""
MynEra Aira - Data Ingestion Script
Loads courses and mentors from JSON files and uploads them to Qdrant with surgical embeddings.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.data_loader import data_loader

def ingest_data():
    """Load and vectorize data from JSON to Qdrant."""
    print("🚀 MynEra Aira - Data Ingestion Pipeline")
    print("=" * 60)
    
    try:
        # Step 1: Load and embed courses
        print("\n📚 Step 1: Loading and embedding courses...")
        data_loader.load_and_embed_courses()
        
        # Step 2: Load and embed mentors
        print("\n👨‍🏫 Step 2: Loading and embedding mentors...")
        data_loader.load_and_embed_mentors()
        
        print("\n" + "=" * 60)
        print("✅ Data Ingestion Complete!")
        print("\n💡 Next steps:")
        print("   • Run: python src/scripts/system_check.py (verify setup)")
        print("   • Run: python test_console.py (test chatbot)")
        
    except Exception as e:
        print(f"\n❌ Data ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    ingest_data()
