# create_users.py
import sys
sys.path.append('src')

from gtm_voyager.utils.security import SecurityManager
import psycopg2

# Create security manager
security = SecurityManager()

# Generate password hashes
admin_hash = security.hash_password("GTMVoyager2024!")
demo_hash = security.hash_password("demo123")

print(f"Admin hash: {admin_hash}")
print(f"Demo hash: {demo_hash}")

# Update database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="gtm_voyager",
    user="gtm_admin",
    password="hRZTvBn8daL0TL"
)

cur = conn.cursor()
cur.execute("UPDATE users SET password_hash = %s WHERE email = 'admin@gtmvoyager.com'", (admin_hash,))
cur.execute("UPDATE users SET password_hash = %s WHERE email = 'demo@dental.com'", (demo_hash,))
conn.commit()
conn.close()

print("Password hashes updated successfully!")
