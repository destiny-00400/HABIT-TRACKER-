import json
import os
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk
FILE_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "habits.json")
habits = []  
def load_habits():
    """Read habits from habits.json (called once when the program starts)."""
    global habits
    if not os.path.exists(FILE_NAME):
        habits = []          # first run: nothing saved yet
        return
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            data = json.load(file)
        loaded = []
        for item in data["habits"]:
            # keep only habits that have the fields we need
            if "name" in item and "completed_dates" in item:
                if "created" not in item:
                    item["created"] = today_string()
                loaded.append(item)
        habits = loaded
    except (json.JSONDecodeError, KeyError, TypeError, OSError):
        # The file is damaged: keep a backup copy and start with an empty list
        habits = []
        try:
            os.replace(FILE_NAME, FILE_NAME + ".bak")
        except OSError:
            pass
        messagebox.showwarning("Data problem",
                               "habits.json could not be read.\n"
                               "A backup was saved as habits.json.bak and a new list was started.")


def save_habits():
    """Write all habits to habits.json (called after every change)."""
    try:
        with open(FILE_NAME, "w", encoding="utf-8") as file:
            json.dump({"habits": habits}, file, indent=2)
    except OSError:
        messagebox.showerror("Save error", "Could not save your data to habits.json.")

def today_string():
    """Today's date as text, e.g. '2026-10-26'."""
    return date.today().isoformat()


def is_completed_today(habit):
    return today_string() in habit["completed_dates"]


def get_streak(habit):
    """Number of days in a row the habit was completed (a pending today does not break it)."""
    dates = habit["completed_dates"]
    day = date.today()
    if day.isoformat() not in dates:
        day = day - timedelta(days=1)       # start counting from yesterday
    streak = 0
    while day.isoformat() in dates:
        streak = streak + 1
        day = day - timedelta(days=1)
    return streak


def get_selected_index():
    """Return the position of the selected habit in the list, or None if nothing is selected."""
    selection = table.selection()
    if len(selection) == 0:
        messagebox.showinfo("Select a habit", "Please click a habit in the list first.")
        return None
    return int(selection[0])    


def refresh_display(selected_index=None):
    """Redraw the habit list, progress bar and status message."""
    for row in table.get_children():
        table.delete(row)
    completed = 0
    for index in range(len(habits)):
        habit = habits[index]
        if is_completed_today(habit):
            status = "Completed"
            completed = completed + 1
        else:
            status = "Pending"
        table.insert("", "end", iid=str(index), values=(habit["name"], status))

    # 2. Keep the same row selected (if there is one)
    if selected_index is not None and selected_index < len(habits):
        table.selection_set(str(selected_index))

    # 3. Update the progress section
    total = len(habits)
    if total > 0:
        percent = round(completed / total * 100)
    else:
        percent = 0
    progress_bar["value"] = percent
    percent_label.config(text="Today's progress: " + str(percent) + "%")
    status_label.config(text=str(completed) + " of " + str(total) + " habits completed today")
    date_label.config(text="Date: " + today_string())


def add_habit():
    """Add a new habit from the text box."""
    name = name_entry.get().strip()

    if name == "":
        messagebox.showwarning("Empty name", "Please type a habit name.")
        return
    for habit in habits:                      # prevent duplicate names
        if habit["name"].lower() == name.lower():
            messagebox.showwarning("Duplicate", "This habit already exists.")
            return

    habits.append({"name": name, "created": today_string(), "completed_dates": []})
    save_habits()
    name_entry.delete(0, tk.END)
    refresh_display(len(habits) - 1)


def toggle_complete():
    """Mark the selected habit complete for today, or undo it."""
    index = get_selected_index()
    if index is None:
        return
    habit = habits[index]
    today = today_string()
    if today in habit["completed_dates"]:
        habit["completed_dates"].remove(today)      # undo
    else:
        habit["completed_dates"].append(today)      # only added once per day
    save_habits()
    refresh_display(index)


def delete_habit():
    """Delete the selected habit after asking for confirmation."""
    index = get_selected_index()
    if index is None:
        return
    name = habits[index]["name"]
    if messagebox.askyesno("Confirm delete", "Delete '" + name + "' and its history?"):
        habits.pop(index)
        save_habits()
        refresh_display()


def view_details():
    """Show details of the selected habit in a message box."""
    index = get_selected_index()
    if index is None:
        return
    habit = habits[index]
    if is_completed_today(habit):
        status = "Completed"
    else:
        status = "Pending"
    streak = get_streak(habit)
    if streak == 1:
        streak_text = "1 day"
    else:
        streak_text = str(streak) + " days"
    text = ("Habit: " + habit["name"] + "\n"
            "Created on: " + habit["created"] + "\n"
            "Today's status: " + status + "\n"
            "Total days completed: " + str(len(habit["completed_dates"])) + "\n"
            "Current streak: " + streak_text)
    messagebox.showinfo("Habit details", text)


root = tk.Tk()
root.title("Habit Tracker")
root.geometry("520x560")
root.minsize(480, 520)
root.configure(bg="#f3f0ff")           # light purple background

# Style (colours for the progress bar, table and buttons)
style = ttk.Style()
style.theme_use("clam")
style.configure("Green.Horizontal.TProgressbar", troughcolor="#ddd6fe",
                background="#22c55e", thickness=18)
style.configure("Treeview", rowheight=28, font=("Segoe UI", 11))
style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))

# Heading
tk.Label(root, text="Habit Tracker", font=("Segoe UI", 22, "bold"),
         bg="#f3f0ff", fg="#5b3fd6").pack(pady=(15, 0))
date_label = tk.Label(root, text="", font=("Segoe UI", 10), bg="#f3f0ff", fg="#6b6890")
date_label.pack()

# Add-habit row: text field + button
add_frame = tk.Frame(root, bg="#f3f0ff")
add_frame.pack(fill="x", padx=20, pady=12)
name_entry = tk.Entry(add_frame, font=("Segoe UI", 12))
name_entry.pack(side="left", fill="x", expand=True, ipady=4)
name_entry.bind("<Return>", lambda event: add_habit())      # Enter key also adds
tk.Button(add_frame, text="Add Habit", command=add_habit, bg="#7c5cff", fg="white",
          font=("Segoe UI", 11, "bold"), relief="flat", padx=12).pack(side="left", padx=(8, 0))

# Habit list (table with two columns)
list_frame = tk.Frame(root, bg="#f3f0ff")
list_frame.pack(fill="both", expand=True, padx=20)
table = ttk.Treeview(list_frame, columns=("name", "status"), show="headings",
                     selectmode="browse", height=8)
table.heading("name", text="Habit")
table.heading("status", text="Status")
table.column("name", width=300)
table.column("status", width=120, anchor="center")
scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=table.yview)
table.configure(yscrollcommand=scrollbar.set)
table.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Action buttons
button_frame = tk.Frame(root, bg="#f3f0ff")
button_frame.pack(pady=12)
tk.Button(button_frame, text="Complete / Undo", command=toggle_complete, bg="#22c55e", fg="white",
          font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=4).pack(side="left", padx=4)
tk.Button(button_frame, text="View Details", command=view_details, bg="#3b82f6", fg="white",
          font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=4).pack(side="left", padx=4)
tk.Button(button_frame, text="Delete", command=delete_habit, bg="#ef4444", fg="white",
          font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=4).pack(side="left", padx=4)

# Progress section
progress_frame = tk.Frame(root, bg="#ffffff", padx=15, pady=10)
progress_frame.pack(fill="x", padx=20, pady=(0, 15))
percent_label = tk.Label(progress_frame, text="", font=("Segoe UI", 11, "bold"), bg="#ffffff")
percent_label.pack(anchor="w")
progress_bar = ttk.Progressbar(progress_frame, style="Green.Horizontal.TProgressbar",
                               length=400, maximum=100, mode="determinate")
progress_bar.pack(fill="x", pady=6)
status_label = tk.Label(progress_frame, text="", font=("Segoe UI", 10), bg="#ffffff", fg="#6b6890")
status_label.pack(anchor="w")


load_habits()
refresh_display()
name_entry.focus()
root.mainloop()
