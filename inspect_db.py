import os, sqlite3
path = os.path.join('instance','cards.db')
print('db path', os.path.abspath(path), 'exists', os.path.exists(path))
conn = sqlite3.connect(path)
cur = conn.cursor()
try:
    cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
    print('tables', cur.fetchall())
    cur.execute('SELECT id, username, email FROM user')
    print('users', cur.fetchall())
except Exception as e:
    print('error', e)
finally:
    conn.close()
