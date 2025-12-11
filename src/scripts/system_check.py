"""
MynEra Aira - System Health Check
Verifies data files, database connection, and vector search functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.services.vector_store import vector_store
from src.services.matching_engine import matching_engine

def check_data_files():
    """Check if required data files exist."""
    print("\n📁 Check 1: Data Files")
    print("-" * 60)
    
    data_dir = project_root / "data"
    required_files = ["courses.json", "mentors.json"]
    
    all_exist = True
    for filename in required_files:
        file_path = data_dir / filename
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"   ✅ {filename} ({size_kb:.1f} KB)")
        else:
            print(f"   ❌ {filename} (NOT FOUND)")
            all_exist = False
    
    if not all_exist:
        print("\n   ⚠️  Missing data files!")
        print("   💡 Run: python src/scripts/generate_seed_data.py")
        return False
    
    return True

def check_database_connection():
    """Check Qdrant connection."""
    print("\n🗄️  Check 2: Database Connection")
    print("-" * 60)
    
    try:
        # Try to get collections
        collections = vector_store.client.get_collections()
        print(f"   ✅ Connected to Qdrant")
        print(f"   📊 Collections available: {len(collections.collections)}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to connect to Qdrant")
        print(f"   Error: {e}")
        print("\n   💡 Check:")
        print("      • Is Qdrant running?")
        print("      • Are credentials in .env correct?")
        return False

def check_vector_collections():
    """Check if vector collections have data."""
    print("\n📊 Check 3: Vector Collections")
    print("-" * 60)
    
    collections_to_check = [
        (settings.COLLECTION_COURSES, "Courses"),
        (settings.COLLECTION_MENTORS, "Mentors")
    ]
    
    all_populated = True
    for collection_name, display_name in collections_to_check:
        try:
            collection_info = vector_store.client.get_collection(collection_name)
            point_count = collection_info.points_count
            
            if point_count > 0:
                print(f"   ✅ {display_name}: {point_count} vectors")
            else:
                print(f"   ⚠️  {display_name}: 0 vectors (empty)")
                all_populated = False
        except Exception as e:
            print(f"   ❌ {display_name}: Collection not found")
            all_populated = False
    
    if not all_populated:
        print("\n   💡 Run: python src/scripts/ingest_data.py")
        return False
    
    return True

def check_semantic_search():
    """Test semantic search functionality."""
    print("\n🔍 Check 4: Semantic Search Test")
    print("-" * 60)
    
    test_query = "Python backend"
    
    try:
        recommendations, context = matching_engine.find_matches(test_query, limit=1)
        
        if recommendations:
            rec = recommendations[0]
            print(f"   ✅ Search working!")
            print(f"   Query: '{test_query}'")
            print(f"   Top result: {rec.title}")
            print(f"   Match quality: {rec.meta.get('match_quality', 'N/A')}")
            return True
        else:
            print(f"   ⚠️  Search returned no results")
            print(f"   This might indicate vector quality issues")
            return False
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all system checks."""
    print("=" * 60)
    print("🔧 MynEra Aira - System Health Check")
    print("=" * 60)
    
    checks = [
        ("Data Files", check_data_files),
        ("Database Connection", check_database_connection),
        ("Vector Collections", check_vector_collections),
        ("Semantic Search", check_semantic_search),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n   ❌ Check failed with exception: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {check_name}")
    
    print("\n" + "=" * 60)
    if passed == total:
        print("✅ All checks passed! System is ready.")
        print("\n💡 Next: Run python test_console.py to test the chatbot")
        sys.exit(0)
    else:
        print(f"⚠️  {total - passed}/{total} checks failed.")
        print("\n💡 Follow the suggestions above to fix issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
