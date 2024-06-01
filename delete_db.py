import os

# Path to the SQLite database file
db_path = os.path.join(os.getcwd(), 'instance', 'site.db')

# Check if the file exists
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Database file {db_path} has been deleted.")
else:
    print(f"Database file {db_path} does not exist.")
