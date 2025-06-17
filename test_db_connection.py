import psycopg2

try:
    print("Attempting to connect to PostgreSQL...")
    
    # Test connection with your new password
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="gtm_voyager",
        user="gtm_admin",
        password="hRZTvBn8daL0TL"
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    
    print("✅ Database connection successful!")
    print(f"PostgreSQL version: {version[0]}")
    
    # Test creating a simple table
    cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name VARCHAR(50));")
    cursor.execute("INSERT INTO test_table (name) VALUES ('test') ON CONFLICT DO NOTHING;")
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM test_table;")
    count = cursor.fetchone()
    print(f"Test table has {count[0]} rows")
    
    cursor.close()
    conn.close()
    
    print("🎉 Database is working perfectly!")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("Make sure Docker containers are running:")
    print("docker-compose ps")

input("Press Enter to continue...")
