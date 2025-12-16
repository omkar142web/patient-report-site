from flask import Flask, render_template, request, redirect, send_from_directory, session, url_for
from functools import wraps
import os
import re

app = Flask(__name__)
# For production, use a strong, randomly-generated secret loaded from an environment variable.
# You can generate a good key using: python -c 'import secrets; print(secrets.token_hex())'
app.secret_key = os.environ.get("SECRET_KEY", "a-default-fallback-key-for-development")

BASE_UPLOAD = "uploads"
# For production, use environment variables and hashed passwords.
PASSWORD = os.environ.get("DOCTOR_PASSWORD", "rutu")
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(BASE_UPLOAD, exist_ok=True)

def login_required(f):
    """
    Decorator to ensure a user is logged in before accessing a route.
    Redirects to the login page if the user is not in the session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("doctor"):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def clean_name(name):
    """
    Sanitizes a string to be used as a patient name or filename.
    Replaces any character that is not a letter, number, or underscore with an underscore.
    """
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)

def next_index(folder, patient):
    """
    Calculates the next available index for a new report file.
    It inspects the filenames in the given folder, finds the highest index, and returns the next integer.
    For example, if "patient_3.pdf" is the highest, this will return 4.
    """
    nums = []
    for f in os.listdir(folder):
        if f.startswith(patient + "_"):
            try:
                # Extracts the number from filenames like "patient_1.pdf"
                n = int(f.split("_")[1].split(".")[0])
                nums.append(n)
            except (ValueError, IndexError):
                # Ignore files that do not match the expected naming convention
                pass
    return max(nums) + 1 if nums else 1

def allowed_file(filename):
    """Checks if a file's extension is in the ALLOWED_EXTENSIONS set."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Handles the main page, which includes the file upload form.
    On POST request, it processes and saves uploaded reports for a patient.
    """
    error = None
    success = None
    if request.method == "POST":
        patient = clean_name(request.form["patient"])
        if not patient:
            error = "Invalid patient name."
            return render_template("index.html", error=error)

        files = request.files.getlist("report")
        if not files or all(f.filename == '' for f in files):
             error = "No files selected."
             return render_template("index.html", error=error)

        patient_dir = os.path.join(BASE_UPLOAD, patient)
        os.makedirs(patient_dir, exist_ok=True)

        idx = next_index(patient_dir, patient)
        uploaded_count = 0

        for f in files:
            if f and f.filename and allowed_file(f.filename):
                ext = os.path.splitext(f.filename)[1]
                name = f"{patient}_{idx}{ext}"
                f.save(os.path.join(patient_dir, name))
                idx += 1
                uploaded_count += 1
            elif f.filename != '':
                error = "File type not allowed or invalid file."

        if uploaded_count > 0:
            success = f"{uploaded_count} file(s) uploaded successfully for {patient}."

    return render_template("index.html", error=error, success=success)

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles the doctor's login. On successful login, the user is added
    to the session and redirected to the reports page.
    """
    error = None
    success = None
    if 'message' in session:
        success = session.pop('message', None)
    
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["doctor"] = True
            return redirect(url_for('reports'))
        else:
            error = "Invalid password."
    
    return render_template("login.html", error=error, success=success)

@app.route("/logout")
def logout():
    """Clears the session to log the user out."""
    session.clear()
    session['message'] = "You have been logged out successfully."
    return redirect(url_for('login'))

@app.route("/reports")
@login_required
def reports():
    """
    Displays a list of all patients and their reports.
    Includes a search functionality to filter patients by name.
    This route requires the user to be logged in.
    """
    search = request.args.get("search", "").lower()
    data = {}

    for patient in os.listdir(BASE_UPLOAD):
        if search and search not in patient.lower():
            continue
        folder = os.path.join(BASE_UPLOAD, patient)
        if os.path.isdir(folder):
            data[patient] = os.listdir(folder)

    return render_template("reports.html", data=data, search=search)

@app.route("/uploads/<patient>/<filename>")
@login_required
def preview(patient, filename):
    """
    Serves a specific report file for preview.
    Requires the user to be logged in.
    """
    return send_from_directory(os.path.join(BASE_UPLOAD, patient), filename)

@app.route("/delete/<patient>/<filename>")
@login_required
def delete_file(patient, filename):
    """
    Deletes a specific report file.
    Requires the user to be logged in.
    """
    path = os.path.join(BASE_UPLOAD, patient, filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect(url_for('reports'))

if __name__ == "__main__":
    # The development server is not for production. A WSGI server like Gunicorn will run the app.
    app.run(debug=False, host='0.0.0.0')
