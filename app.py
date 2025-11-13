from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import json, os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change to a random secure key for production

# ---------- Paths ----------
USERS_FILE = os.path.join("data", "users.json")
USER_DIR = os.path.join("data", "users")

os.makedirs(USER_DIR, exist_ok=True)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

# ---------- Utility Functions ----------
def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def create_user_files(username):
    for name in ["tasks", "events"]:
        path = os.path.join(USER_DIR, f"{username}_{name}.json")
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump([], f)

# ---------- Auth Routes ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        users = load_users()

        if username in users:
            return render_template("register.html", error="Username already exists!")
        if len(password) < 4:
            return render_template("register.html", error="Password too short!")

        users[username] = generate_password_hash(password)
        save_users(users)
        create_user_files(username)
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        users = load_users()

        if username not in users or not check_password_hash(users[username], password):
            return render_template("login.html", error="Invalid credentials!")
        
        session["username"] = username
        return redirect(url_for("profile"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# ---------- Protected Route Example ----------
@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    return render_template("profile.html", username=username)

# ---------- Home ----------
@app.route("/")
def home():
    return render_template("index.html", user=session.get("username"))

if __name__ == "__main__":
    app.run(debug=True)
