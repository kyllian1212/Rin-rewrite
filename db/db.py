"""
Database Module
"""

import sqlite3
import os
import logging

DATABASE_PATH="db/database.db"
BUILD_PATH="db/build.sql"
SONG_LIBRARY_PATH="db/default_song_library.sql"

con = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cur = con.cursor()

# -- init + clear database functions --
def build_database(): 
    if os.path.exists(DATABASE_PATH):
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            if cur.fetchone() == None:
                print("building database...")
                with open(BUILD_PATH, 'r') as sql_build_file:
                    sql_script = sql_build_file.read()

                con.executescript(sql_script)
                create_song_library()
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

# -- song library functions --
def create_song_library():
    try:
        cur.execute("SELECT * FROM bot_default_song_library")
        if cur.fetchone() == None:
            with open(SONG_LIBRARY_PATH, 'r') as sql_song_library_file:
                sql_script = sql_song_library_file.read()
            
            con.executescript(sql_script)
    except:
        raise Exception("error")

def clear_song_library():
    try:
        cur.execute("SELECT * FROM bot_default_song_library")
        if not cur.fetchone() == None:
            update_db("DELETE FROM bot_default_song_library")
        
        cur.execute("SELECT * FROM bot_user_song_library")
        if not cur.fetchone() == None:
            update_db("DELETE FROM bot_user_song_library")
    except:
        raise Exception("error")

# -- db access functions -- #
def fetchone_singlecolumn(column, command, *values):
    cur.execute(command, tuple(values))
    result = cur.fetchone()
    if result == None:
        return None
    return result[column]

def fetchone_fullrow(command, *values):
    cur.execute(command, tuple(values))
    result = cur.fetchone()
    if result == None:
        return None
    return result

def fetchall(command, *values):
    cur.execute(command, tuple(values))
    return cur.fetchall()

def update_db(command, *values):
    try:
        cur.execute(command, tuple(values))
        con.commit()
    except:
        raise Exception("error while updating database.")