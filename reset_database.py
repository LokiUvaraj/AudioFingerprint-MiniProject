from db_sqlite import SqliteDatabase

if __name__ == "__main__":
    db = SqliteDatabase()

    db.query("DROP TABLE IF EXISTS songs;")
    print("removed songs.")
    db.query("""
        CREATE TABLE songs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            filehash TEXT
        );
    """)
    print("created songs.")

    db.query("DROP TABLE IF EXISTS fingerprints;")
    print("removed fingerprints.")
    db.query("""
        CREATE TABLE fingerprints(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_fk INTEGER,
            hash TEXT,
            offset INTEGER
        );
    """)
    print("created fingerprints.")

    print("done")