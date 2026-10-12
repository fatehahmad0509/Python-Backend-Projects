notebook = []


try:
    with open("notes.txt", "r") as f:
        notebook = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    pass


def mainmenu():
    whichprocess = int(input("""---Welcome to the Notebook!

-Add Note: 1
-View Notes: 2
-Delete Note: 3
-Exit: 4
"""))

    if whichprocess == 1:
        addnote()
    elif whichprocess == 2:
        viewnotes()
    elif whichprocess == 3:
        deletenote()
    elif whichprocess == 4:
        exiting()
    else:
        mainmenu()

def addnote():
    global notebook
    notetoadd = input("Enter the note you want to add: ")
    notebook.append(notetoadd)
    with open("notes.txt", "a") as f:
        f.write(notetoadd + "\n")
    input("Your note has been added successfully! Press Enter to return to the main menu...")
    mainmenu()

def viewnotes():
    global notebook
    if not notebook:
        input("No notes have been added yet. Press Enter to return to the main menu...")
        mainmenu()
    else:
        for i, notes in enumerate(notebook, 0):
            print(i, notes)
        input("Press Enter to return to the main menu...")
        mainmenu()

def deletenote():
    global notebook
    try:
        whichnotewilldelete = int(input("Please enter the number of the note you wish to delete (numbering starts from 0): "))
        del notebook[whichnotewilldelete]
        input("Note Successfully Deleted! Press Enter to return to the Main Menu...")
        with open("notes.txt", "w") as f:
            for note in notebook:
                f.write(note + "\n")
        mainmenu()
    except (IndexError, ValueError):
        input("Incorrect entry! Press Enter to return to the Main Menu...")
    mainmenu()




def exiting():
    exit()

mainmenu()