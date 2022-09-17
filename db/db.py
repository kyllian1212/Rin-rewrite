import sqlite3
import os
import logging

DATABASE_PATH="db/database.db"
BUILD_PATH="db/build.sql"

con = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cur = con.cursor()

def build_database(): 
    if os.path.exists(DATABASE_PATH):
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            if cur.fetchone() == None:
                print("building database...")
                with open(BUILD_PATH, 'r') as sql_build_file:
                    sql_script = sql_build_file.read()

                con.executescript(sql_script)
                print("database built successfully!")
        except:
            drop_all_tables()
            raise Exception("error while creating the tables within the database.")
    else:
        raise Exception("database file not found! it probably hasn't been created automatically for some reason.")

def drop_all_tables(): 
    print("dropping all tables...")
    cur.execute("SELECT name FROM sqlite_master where type='table'")
    for table in cur.fetchall():
        cur.execute("DROP TABLE " + table[0]) #string formatting because placeholders can only be used to substitute values
    print("all tables dropped successfully")

def fetchone(command, *values):
    cur.execute(command, tuple(values))
    result = cur.fetchone()
    if result == None:
        return None
    return result[0]

def fetchall(command, *values):
    cur.execute(command, tuple(values))
    return cur.fetchall()

def update_db(command, *values):
    try:
        cur.execute(command, tuple(values))
        con.commit()
    except:
        raise Exception("error while updating database.")