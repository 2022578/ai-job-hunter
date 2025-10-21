"""
Test sidebar database operations that might cause recursion
"""
import sys
sys.setrecursionlimit(10000)

print(f"Testing with recursion limit: {sys.getrecursionlimit()}")
print("="*60)

try:
    print("\n1. Importing database components...")
    from database.db_manager import DatabaseManager
    from database.repositories.job_repository import JobRepository
    from database.repositories.application_repository import ApplicationRepository
    print("   ✓ Imports successful")
    
    print("\n2. Creating database manager...")
    db_manager = DatabaseManager('data/job_assistant.db')
    print("   ✓ Database manager created")
    
    print("\n3. Creating repositories...")
    job_repo = JobRepository(db_manager)
    app_repo = ApplicationRepository(db_manager)
    print("   ✓ Repositories created")
    
    print("\n4. Fetching all jobs (this might cause recursion)...")
    jobs = job_repo.find_all()
    print(f"   ✓ Found {len(jobs)} jobs")
    
    print("\n5. Getting application statistics...")
    stats = app_repo.get_statistics('default_user')
    print(f"   ✓ Stats retrieved: {stats}")
    
    print("\n6. Testing individual job access...")
    if jobs:
        first_job = jobs[0]
        print(f"   ✓ First job: {first_job.title} at {first_job.company}")
        print(f"   ✓ Job attributes accessible")
    else:
        print("   ℹ No jobs in database")
    
    print("\n" + "="*60)
    print("✅ All sidebar operations completed successfully!")
    print("="*60)
    
except RecursionError as e:
    print(f"\n❌ RecursionError occurred!")
    print(f"   Error: {str(e)[:100]}")
    print("\n   This indicates a circular reference in your data models or database queries.")
    print("   Possible causes:")
    print("   - Circular references between model objects")
    print("   - Infinite loop in __repr__ or __str__ methods")
    print("   - Database query returning self-referential data")
    
except Exception as e:
    print(f"\n❌ Error occurred: {type(e).__name__}")
    print(f"   {str(e)[:200]}")
    import traceback
    print("\nLast 15 lines of traceback:")
    tb_lines = traceback.format_exc().split('\n')
    for line in tb_lines[-15:]:
        if line.strip():
            print(f"   {line}")
