import psycopg2

conn = psycopg2.connect("postgresql://pilot_database_user:Tw8juX2AKotvIS657cN4YrGBC43GQ2AJ@dpg-d85pipj7uimc73bm3h80-a.virginia-postgres.render.com/pilot_database")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cur.execute("""
INSERT INTO expenses (name, amount)
VALUES (%s, %s)
""", ("Groceries", 45.20))

conn.commit()

cur.execute("SELECT * FROM expenses;")
print(cur.fetchall())

cur.close()
conn.close()



