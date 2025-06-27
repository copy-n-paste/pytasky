import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import threading
import time
import os
import requests
from plyer import notification
from dotenv import load_dotenv
from tasks import Task, add_task, get_all_tasks, delete_task, mark_task_completed, get_tasks_by_status

# Load Gemini API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=' + GEMINI_API_KEY

REPEAT_OPTIONS = ['One-time', 'Daily', 'Weekly', 'Monthly', 'Yearly']

# Gemini API call to summarize/refine description
def summarize_description(description):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": f"Summarize and refine this task description for a notification: {description}"}]}]
    }
    try:
        response = requests.post(GEMINI_API_URL, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        summary = result['candidates'][0]['content']['parts'][0]['text']
        return summary.strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        return description  # fallback

# Notification scheduler thread
def notification_worker():
    while True:
        tasks = get_all_tasks()
        now = datetime.now()
        for task in tasks:
            if task.status != 'pending':
                continue
            # Parse date and time
            try:
                task_dt = datetime.strptime(f"{task.date} {task.time}", "%d-%m-%Y %I:%M:%S %p")
            except Exception as e:
                continue
            # If task is due (within 1 minute)
            if 0 <= (task_dt - now).total_seconds() < 60:
                # Send notification
                notification.notify(
                    title=task.name,
                    message=task.description,
                    timeout=10
                )
                # Handle repeat
                if task.repeat == 'One-time':
                    mark_task_completed(task.name, task.date, task.time)
                else:
                    # Reschedule task
                    next_dt = get_next_datetime(task_dt, task.repeat)
                    if next_dt:
                        mark_task_completed(task.name, task.date, task.time)
                        new_task = Task(
                            name=task.name,
                            description=task.description,
                            time=next_dt.strftime("%I:%M:%S %p"),
                            date=next_dt.strftime("%d-%m-%Y"),
                            repeat=task.repeat
                        )
                        add_task(new_task)
        time.sleep(30)  # Check every 30 seconds

def get_next_datetime(dt, repeat):
    if repeat == 'Daily':
        return dt + timedelta(days=1)
    elif repeat == 'Weekly':
        return dt + timedelta(weeks=1)
    elif repeat == 'Monthly':
        # Add 1 month (approximate)
        month = dt.month + 1 if dt.month < 12 else 1
        year = dt.year if dt.month < 12 else dt.year + 1
        try:
            return dt.replace(year=year, month=month)
        except ValueError:
            # Handle month overflow (e.g., Feb 30)
            return dt.replace(year=year, month=month, day=28)
    elif repeat == 'Yearly':
        try:
            return dt.replace(year=dt.year + 1)
        except ValueError:
            return dt.replace(year=dt.year + 1, day=28)
    return None

# Validation for date and time (no past allowed)
def is_future_datetime(date_str, time_str):
    try:
        task_dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %I:%M:%S %p")
        return task_dt > datetime.now()
    except Exception:
        return False

# Edit task dialog
def edit_task_dialog(root, task, refresh_callback):
    edit_win = tk.Toplevel(root)
    edit_win.title(f"Edit Task: {task.name}")
    edit_win.geometry("350x400")

    tk.Label(edit_win, text="Task Name:").pack(anchor='w', padx=10, pady=(10,0))
    name_entry = tk.Entry(edit_win, width=35)
    name_entry.insert(0, task.name)
    name_entry.pack(padx=10)

    tk.Label(edit_win, text="Description:").pack(anchor='w', padx=10, pady=(10,0))
    desc_text = tk.Text(edit_win, width=35, height=4)
    desc_text.insert("1.0", task.description)
    desc_text.pack(padx=10)

    tk.Label(edit_win, text="Time (HH:MM:SS AM/PM):").pack(anchor='w', padx=10, pady=(10,0))
    time_entry = tk.Entry(edit_win, width=20)
    time_entry.insert(0, task.time)
    time_entry.pack(padx=10)

    tk.Label(edit_win, text="Date (DD-MM-YYYY):").pack(anchor='w', padx=10, pady=(10,0))
    date_entry = tk.Entry(edit_win, width=20)
    date_entry.insert(0, task.date)
    date_entry.pack(padx=10)

    tk.Label(edit_win, text="Repeat Frequency:").pack(anchor='w', padx=10, pady=(10,0))
    repeat_var = tk.StringVar(value=task.repeat)
    repeat_menu = ttk.Combobox(edit_win, textvariable=repeat_var, values=REPEAT_OPTIONS, state='readonly')
    repeat_menu.pack(padx=10)

    def save_edits():
        name = name_entry.get().strip()
        desc = desc_text.get("1.0", tk.END).strip()
        time_str = time_entry.get().strip()
        date_str = date_entry.get().strip()
        repeat = repeat_var.get()
        if not (name and desc and time_str and date_str):
            messagebox.showerror("Error", "All fields are required.", parent=edit_win)
            return
        # Validate time and date
        if not is_future_datetime(date_str, time_str):
            messagebox.showerror("Error", "Date and time must be in the future.", parent=edit_win)
            return
        # Summarize/refine description
        edit_win.config(cursor="wait")
        edit_win.update()
        summary = summarize_description(desc)
        edit_win.config(cursor="")
        # Delete old task and add new one
        delete_task(task.name, task.date, task.time)
        new_task = Task(name, summary, time_str, date_str, repeat)
        add_task(new_task)
        messagebox.showinfo("Success", "Task updated!", parent=edit_win)
        edit_win.destroy()
        refresh_callback()

    save_btn = tk.Button(edit_win, text="Save Changes", command=save_edits)
    save_btn.pack(pady=10)

# Delete confirmation dialog
def confirm_delete(root, task, refresh_callback):
    confirm_win = tk.Toplevel(root)
    confirm_win.title("Confirm Delete")
    confirm_win.geometry("300x150")
    tk.Label(confirm_win, text=f"Type 'delete' to confirm deletion of:\n{task.name}").pack(pady=10)
    entry = tk.Entry(confirm_win, width=20)
    entry.pack(pady=5)
    def do_delete():
        if entry.get().strip().lower() == "delete":
            delete_task(task.name, task.date, task.time)
            messagebox.showinfo("Deleted", f"Task '{task.name}' deleted.", parent=confirm_win)
            confirm_win.destroy()
            refresh_callback()
        else:
            messagebox.showerror("Error", "You must type 'delete' to confirm.", parent=confirm_win)
    btn = tk.Button(confirm_win, text="Delete", command=do_delete)
    btn.pack(pady=5)

# GUI setup
def main():
    root = tk.Tk()
    root.title("Taskii - Smart Task Manager")
    root.geometry("950x650")
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TLabel', font=('Segoe UI', 11))
    style.configure('TButton', font=('Segoe UI', 11, 'bold'), padding=6)
    style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'))
    style.configure('Treeview', font=('Segoe UI', 10), rowheight=28)
    style.configure('TFrame', background='#f7f7fa')
    root.configure(bg='#f7f7fa')

    # --- Task Entry Frame ---
    entry_frame = ttk.LabelFrame(root, text="Add New Task", padding=16)
    entry_frame.pack(fill='x', padx=20, pady=10)

    ttk.Label(entry_frame, text="Task Name:").grid(row=0, column=0, sticky='w', pady=2)
    name_entry = ttk.Entry(entry_frame, width=32)
    name_entry.grid(row=0, column=1, padx=5, pady=2)

    ttk.Label(entry_frame, text="Description:").grid(row=1, column=0, sticky='w', pady=2)
    desc_text = tk.Text(entry_frame, width=32, height=3, font=('Segoe UI', 10))
    desc_text.grid(row=1, column=1, padx=5, pady=2)

    ttk.Label(entry_frame, text="Date:").grid(row=0, column=2, sticky='w', pady=2)
    date_entry = DateEntry(entry_frame, width=14, date_pattern='dd-mm-yyyy', font=('Segoe UI', 10), mindate=datetime.now().date())
    date_entry.grid(row=0, column=3, padx=5, pady=2)
    date_entry.tooltip = ttk.Label(entry_frame, text="Select the date from the calendar.", font=('Segoe UI', 8), foreground='#888')

    ttk.Label(entry_frame, text="Time:").grid(row=1, column=2, sticky='w', pady=2)
    # Time pickers
    hour_var = tk.StringVar(value=datetime.now().strftime('%I'))
    minute_var = tk.StringVar(value=datetime.now().strftime('%M'))
    second_var = tk.StringVar(value=datetime.now().strftime('%S'))
    ampm_var = tk.StringVar(value=datetime.now().strftime('%p'))
    hour_box = ttk.Combobox(entry_frame, textvariable=hour_var, width=3, values=[f"{i:02d}" for i in range(1,13)], state='readonly')
    minute_box = ttk.Combobox(entry_frame, textvariable=minute_var, width=3, values=[f"{i:02d}" for i in range(0,60)], state='readonly')
    second_box = ttk.Combobox(entry_frame, textvariable=second_var, width=3, values=[f"{i:02d}" for i in range(0,60)], state='readonly')
    ampm_box = ttk.Combobox(entry_frame, textvariable=ampm_var, width=3, values=['AM','PM'], state='readonly')
    hour_box.grid(row=1, column=3, sticky='w', padx=(5,0))
    minute_box.grid(row=1, column=3, padx=(40,0), sticky='w')
    second_box.grid(row=1, column=3, padx=(75,0), sticky='w')
    ampm_box.grid(row=1, column=3, padx=(110,0), sticky='w')
    # Tooltips
    for widget, tip in zip([hour_box, minute_box, second_box, ampm_box], ["Hour", "Minute", "Second", "AM/PM"]):
        widget.tooltip = ttk.Label(entry_frame, text=tip, font=('Segoe UI', 8), foreground='#888')

    ttk.Label(entry_frame, text="Repeat:").grid(row=2, column=0, sticky='w', pady=2)
    repeat_var = tk.StringVar(value=REPEAT_OPTIONS[0])
    repeat_menu = ttk.Combobox(entry_frame, textvariable=repeat_var, values=REPEAT_OPTIONS, state='readonly', width=15)
    repeat_menu.grid(row=2, column=1, padx=5, pady=2, sticky='w')

    def submit_task():
        name = name_entry.get().strip()
        desc = desc_text.get("1.0", tk.END).strip()
        date_str = date_entry.get_date().strftime('%d-%m-%Y')
        time_str = f"{hour_var.get()}:{minute_var.get()}:{second_var.get()} {ampm_var.get()}"
        repeat = repeat_var.get()
        if not (name and desc):
            messagebox.showerror("Error", "All fields are required.")
            return
        if not is_future_datetime(date_str, time_str):
            messagebox.showerror("Error", "Date and time must be in the future.")
            return
        root.config(cursor="wait")
        root.update()
        summary = summarize_description(desc)
        root.config(cursor="")
        task = Task(name, summary, time_str, date_str, repeat)
        add_task(task)
        messagebox.showinfo("Success", "Task added!")
        name_entry.delete(0, tk.END)
        desc_text.delete("1.0", tk.END)
        repeat_var.set(REPEAT_OPTIONS[0])
        refresh_task_tables()

    submit_btn = ttk.Button(entry_frame, text="Add Task", command=submit_task)
    submit_btn.grid(row=2, column=3, pady=5, sticky='e')

    # --- Task Tables ---
    table_frame = ttk.Frame(root)
    table_frame.pack(fill='both', expand=True, padx=20, pady=10)

    reload_btn = ttk.Button(table_frame, text="Reload", command=lambda: refresh_task_tables())
    reload_btn.grid(row=0, column=1, sticky='e', padx=(0, 10), pady=(0,2))

    pending_label = ttk.Label(table_frame, text="Pending Tasks", font=('Segoe UI', 12, 'bold'))
    pending_label.grid(row=0, column=0, sticky='w', pady=(0,2))
    pending_tree = ttk.Treeview(table_frame, columns=("Name", "Description", "Date", "Time", "Repeat", "Actions"), show='headings', height=7, style='Treeview')
    for col in ("Name", "Description", "Date", "Time", "Repeat"):
        pending_tree.heading(col, text=col)
        pending_tree.column(col, width=120 if col!="Description" else 220)
    pending_tree.heading("Actions", text="Actions")
    pending_tree.column("Actions", width=120)
    pending_tree.grid(row=1, column=0, sticky='nsew', columnspan=2)

    completed_label = ttk.Label(table_frame, text="Completed Tasks", font=('Segoe UI', 12, 'bold'))
    completed_label.grid(row=2, column=0, sticky='w', pady=(10,2))
    completed_tree = ttk.Treeview(table_frame, columns=("Name", "Description", "Date", "Time", "Repeat"), show='headings', height=5, style='Treeview')
    for col in ("Name", "Description", "Date", "Time", "Repeat"):
        completed_tree.heading(col, text=col)
        completed_tree.column(col, width=120 if col!="Description" else 220)
    completed_tree.grid(row=3, column=0, sticky='nsew', columnspan=2)

    table_frame.grid_rowconfigure(1, weight=1)
    table_frame.grid_rowconfigure(3, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_columnconfigure(1, weight=1)

    # Action buttons for pending tasks
    def on_pending_tree_select(event):
        selected = pending_tree.selection()
        if not selected:
            return
        item = pending_tree.item(selected[0])
        values = item['values']
        for t in get_tasks_by_status('pending'):
            if (t.name, t.description, t.date, t.time, t.repeat) == tuple(values[:5]):
                action_menu = tk.Menu(root, tearoff=0)
                action_menu.add_command(label="Edit", command=lambda: edit_task_dialog(root, t, refresh_task_tables))
                action_menu.add_command(label="Delete", command=lambda: confirm_delete(root, t, refresh_task_tables))
                try:
                    action_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    action_menu.grab_release()
                break

    def on_completed_tree_select(event):
        selected = completed_tree.selection()
        if not selected:
            return
        item = completed_tree.item(selected[0])
        values = item['values']
        for t in get_tasks_by_status('completed'):
            if (t.name, t.description, t.date, t.time, t.repeat) == tuple(values[:5]):
                action_menu = tk.Menu(root, tearoff=0)
                action_menu.add_command(label="Delete", command=lambda: confirm_delete(root, t, refresh_task_tables))
                try:
                    action_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    action_menu.grab_release()
                break

    pending_tree.bind("<Button-3>", on_pending_tree_select)
    completed_tree.bind("<Button-3>", on_completed_tree_select)

    def format_countdown(task_dt):
        now = datetime.now()
        diff = task_dt - now
        if diff.total_seconds() <= 0:
            return "Due now"
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        if days > 0:
            return f"{days} day{'s' if days != 1 else ''} {hours} hour{'s' if hours != 1 else ''} left"
        elif hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''} left"
        else:
            return f"{minutes} minute{'s' if minutes != 1 else ''} left"

    def refresh_task_tables():
        for i in pending_tree.get_children():
            pending_tree.delete(i)
        for t in get_tasks_by_status('pending'):
            try:
                task_dt = datetime.strptime(f"{t.date} {t.time}", "%d-%m-%Y %I:%M:%S %p")
                countdown = format_countdown(task_dt)
            except:
                countdown = "Invalid date/time"
            pending_tree.insert('', 'end', values=(t.name, t.description, t.date, t.time, t.repeat, countdown))
        for i in completed_tree.get_children():
            completed_tree.delete(i)
        for t in get_tasks_by_status('completed'):
            completed_tree.insert('', 'end', values=(t.name, t.description, t.date, t.time, t.repeat))

    refresh_task_tables()

    # Start notification thread
    t = threading.Thread(target=notification_worker, daemon=True)
    t.start()

    root.mainloop()

if __name__ == "__main__":
    main() 
