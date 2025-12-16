from flask import Flask, render_template, request, redirect, send_from_directory, session, url_for, flash, jsonify
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import os
import re

app = Flask(__name__)
# For production, use a strong, randomly-generated secret loaded from an environment variable.
# You can generate a good key using: python -c 'import secrets; print(secrets.token_hex())'
app.secret_key = os.environ.get("SECRET_KEY", "a-default-fallback-key-for-development")

BASE_UPLOAD = "uploads"
# Store a HASH of the password in production, not the password itself.
PASSWORD_HASH = os.environ.get("DOCTOR_PASSWORD_HASH")
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
        # Use a regex to find the number between the patient name and the extension.
        # This is more robust than splitting by underscores.
        # It looks for filenames like "patient_name_123.pdf"
        match = re.match(rf"^{re.escape(patient)}_(\d+)\..+$", f)
        if match:
            nums.append(int(match.group(1)))

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
    if request.method == "POST":
        patient = clean_name(request.form["patient"])
        if not patient:
            return jsonify({"error": "Invalid patient name."}), 400

        files = request.files.getlist("report")
        if not files or all(f.filename == '' for f in files):
             return jsonify({"error": "No files selected."}), 400

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
            success_message = f"{uploaded_count} file(s) uploaded successfully for {patient}."
            return jsonify({"success": success_message})

    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles the doctor's login. On successful login, the user is added
    to the session and redirected to the reports page.
    """
    error = None
    if request.method == "POST":
        # Ensure the hash is set in the environment
        if not PASSWORD_HASH:
            error = "Application is not configured for login."
        # Check the submitted password against the stored hash
        elif check_password_hash(PASSWORD_HASH, request.form.get("password", "")):
            session["doctor"] = True
            return redirect(url_for('reports'))
        else:
            error = "Invalid password."
    
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    """Clears the session to log the user out."""
    session.clear()
    flash("You have been logged out successfully.", "success")
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
    # Retrieve flashed messages to display them
    # This is not strictly necessary if your template handles it,
    # but it's good practice to be aware of the messages.
    messages = session.get('_flashes', [])

    data = {}

    for patient in os.listdir(BASE_UPLOAD):
        folder = os.path.join(BASE_UPLOAD, patient)
        if not os.path.isdir(folder):
            continue

        all_files = os.listdir(folder)
        
        if not search:
            # If no search term, show all files for the patient
            if all_files:
                data[patient] = all_files
        else:
            # If there is a search term, filter results
            patient_name_matches = search in patient.lower()
            matching_files = [f for f in all_files if search in f.lower()]

            if patient_name_matches:
                data[patient] = all_files # Show all files if patient name matches
            elif matching_files:
                data[patient] = matching_files # Otherwise, show only matching files

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
        flash(f"Report '{filename}' was deleted successfully.", "success")

        # Check if the parent directory is now empty
        patient_dir = os.path.dirname(path)
        if not os.listdir(patient_dir):
            os.rmdir(patient_dir)
            flash(f"Patient '{patient}' removed as they have no more reports.", "info")

    return redirect(url_for('reports'))

if __name__ == "__main__":
    # The development server is not for production. A WSGI server like Gunicorn will run the app.
    app.run(debug=False, host='0.0.0.0')
