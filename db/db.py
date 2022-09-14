import sqlite3
import os
import logging

DATABASE_PATH="db/database.db"
BUILD_PATH="db/build.sql"

con = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cur = con.cursor()

def build_database():
    if os.path.exists('db/database.db'):
        print("yeah")
    else:
        raise Exception()