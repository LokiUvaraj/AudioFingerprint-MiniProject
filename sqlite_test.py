import sys, os
sys.path.append(os.path.join(sys.path[0], ".."))

from db_sqlite import SqliteDatabase

if __name__ == "__main__":
    db = SqliteDatabase()

    row = db.executeOne("SELECT 2+3 as x;")

    print(row)
    if row[0] == 5:
        print("SQLite test OK.")
    else:
        print("failed simple sql execution")