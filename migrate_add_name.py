import sqlite3

db_path = r'c:\Users\Govind\Inferno_Eye\inferno_eye.db'
con = sqlite3.connect(db_path)
cur = con.cursor()

cur.execute("PRAGMA table_info(admin_users)")
cols = [row[1] for row in cur.fetchall()]
print("Existing columns:", cols)

if "name" not in cols:
    cur.execute('ALTER TABLE admin_users ADD COLUMN name TEXT DEFAULT ""')
    con.commit()
    print("SUCCESS: Added 'name' column to admin_users table")
else:
    print("OK: 'name' column already exists")

con.close()
