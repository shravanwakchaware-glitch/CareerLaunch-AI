import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

cursor.execute("SELECT * FROM interview_results")

rows = cursor.fetchall()

print("\nInterview Results:\n")

for row in rows:
    print(row)

connection.close()