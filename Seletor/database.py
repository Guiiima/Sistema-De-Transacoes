import sqlite3

def connect(database):
    global conn, cursor
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

def execute(comando, params):
    
    cursor.execute(comando, params)
    conn.commit()


def select(comando):
    cursor.execute(comando)
    return cursor.fetchall()

def close():
    cursor.close()
    conn.close()