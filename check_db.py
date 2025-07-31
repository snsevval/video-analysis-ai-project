import sqlite3

conn = sqlite3.connect('securityvision_users.db')
cursor = conn.cursor()

print("=== TABLOLAR ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

print("\n=== TABLO YAPILARI ===")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
schemas = cursor.fetchall()
for schema in schemas:
    if schema[0]:
        print(f"{schema[0]}\n")

print("\n=== KULLANICI KAYITLARI (İLK 3) ===")
try:
    cursor.execute("SELECT * FROM users LIMIT 3;")
    users = cursor.fetchall()
    for user in users:
        print(f"  {user}")
except:
    print("users tablosu bulunamadı")

conn.close()