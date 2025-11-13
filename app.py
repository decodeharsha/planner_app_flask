from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"  # change this before deploying publicly!

# Base data directory
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)


# -------------------------------
# Utility functions
# -------------------------------
def load_users():
    """Load all users from users.json"""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    """Save users to users.json"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def get_user_file(username, data_type):
    """Return per-user JSON file path"""
    user_dir = os.path.join(DATA_DIR, "users")
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, f"{username}_{data_type}.json")


def load_user_data(username, data_type):
    """Load user-specific data (tasks or events)"""
    file_path = get_user_file(username, data_type)
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return json.load(f)


def save_user_data(username, data_type, data):
    """Save user-specific data (tasks or events)"""
    file_path = get_user_file(username, data_type)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- Registration ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_users()

        if username in users:
            flash("Username already exists. Please choose another one.")
            return redirect(url_for("register"))

        users[username] = generate_password_hash(password)
        save_users(users)

        # create empty files for new user
        save_user_data(username, "tasks", [])
        save_user_data(username, "events", [])

        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------- Login ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_users()
        if username not in users or not check_password_hash(users[username], password):
            flash("Invalid credentials. Try again.")
            return redirect(url_for("login"))

        session["username"] = username
        flash(f"Welcome, {username}!")
        return redirect(url_for("profile"))

    return render_template("login.html")


# ---------- Logout ----------
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.")
    return redirect(url_for("home"))


# ---------- Profile ----------
@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    return render_template("profile.html", username=username)


# ---------- Task Manager ----------
@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    tasks = load_user_data(username, "tasks")

    if request.method == "POST":
        task_name = request.form["task"]
        if task_name.strip():
            tasks.append({"task": task_name, "done": False})
            save_user_data(username, "tasks", tasks)
            flash("Task added successfully!")
        return redirect(url_for("tasks"))

    return render_template("tasks.html", tasks=tasks, username=username)


@app.route("/tasks/complete/<int:task_index>")
def complete_task(task_index):
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    tasks = load_user_data(username, "tasks")
    if 0 <= task_index < len(tasks):
        tasks[task_index]["done"] = not tasks[task_index]["done"]
        save_user_data(username, "tasks", tasks)

    return redirect(url_for("tasks"))


@app.route("/tasks/delete/<int:task_index>")
def delete_task(task_index):
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    tasks = load_user_data(username, "tasks")
    if 0 <= task_index < len(tasks):
        tasks.pop(task_index)
        save_user_data(username, "tasks", tasks)

    return redirect(url_for("tasks"))


# ---------- Event Planner ----------
@app.route("/events", methods=["GET", "POST"])
def events():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    events = load_user_data(username, "events")

    if request.method == "POST":
        title = request.form["title"]
        date = request.form["date"]
        time = request.form["time"]
        if title.strip() and date:
            events.append({"title": title, "date": date, "time": time})
            save_user_data(username, "events", events)
            flash("Event added successfully!")
        return redirect(url_for("events"))

    return render_template("events.html", events=events, username=username)


# ---------- Today's Events ----------
@app.route("/events/today")
def todays_events():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    events = load_user_data(username, "events")
    today_str = datetime.now().strftime("%Y-%m-%d")

    today_events = [e for e in events if e["date"] == today_str]
    return render_template("events.html", events=today_events, username=username, today=True)


# -------------------------------
# Run the app
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
