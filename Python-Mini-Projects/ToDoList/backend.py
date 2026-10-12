import sqlite3

notes = sqlite3.connect('notes.db')
cursor = notes.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS notes (
    note TEXT
)
""")

notes.commit()

class to_do_list:
    def add_note(self, note):
        cursor.execute("INSERT INTO notes (note) VALUES (?)", (note,))
        notes.commit()

    def delete_note(self, note):
        cursor.execute("DELETE FROM notes WHERE note = ?", (note,))
        notes.commit()

    def view_notes(self):
        cursor.execute("SELECT * FROM notes")
        return cursor.fetchall()