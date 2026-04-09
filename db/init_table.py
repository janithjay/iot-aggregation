from db.database import create_table_if_not_exists


if __name__ == "__main__":
    ok = create_table_if_not_exists()
    print("Table ready" if ok else "Table init failed")
