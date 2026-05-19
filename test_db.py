import psycopg2

conn = psycopg2.connect(
    "postgresql://pilot_database_user:Tw8juX2AKotvIS657cN4YrGBC43GQ2AJ@dpg-d85pipj7uimc73bm3h80-a.virginia-postgres.render.com/pilot_database"
)

cur = conn.cursor()
cur.execute("SELECT 1;")
print(cur.fetchone())

cur.close()
conn.close()