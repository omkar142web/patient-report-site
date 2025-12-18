from flask import Flask, render_template, request, redirect, send_from_directory, session, url_for, flash, jsonify
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import re
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)
# For production, use a strong, randomly-generated secret loaded from an environment variable.
# You can generate a good key using: python -c 'import secrets; print(secrets.token_hex())'
app.secret_key = os.environ.get("SECRET_KEY", "a-default-fallback-key-for-development")

cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)
PASSWORD_HASH = os.environ.get("DOCTOR_PASSWORD_HASH")
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

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
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', name)

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
        patient = request.form.get("patient")
        if not patient:
            return jsonify({"error": "Invalid patient name."}), 400

        files = request.files.getlist("report")
        if not files or all(f.filename == '' for f in files):
             return jsonify({"error": "No files selected."}), 400
        
        patient_folder = clean_name(patient)
        uploaded_count = 0

        for f in files:
            if f and f.filename and allowed_file(f.filename):
                # Use a secure version of the original filename for the public_id
                filename_base = os.path.splitext(secure_filename(f.filename))[0]
                public_id = f"{filename_base}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                cloudinary.uploader.upload(
                    f, folder=patient_folder, public_id=public_id, resource_type="auto"
                )
                uploaded_count += 1
            elif f and f.filename:
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
    data = {}

    # More efficient: Search directly and group results in Python.
    # This allows searching by patient name (folder) or filename.
    expression = None
    if search:
        # Search in folder (patient name) OR filename
        expression = f"folder:*{search}* OR filename:*{search}*"

    resources = cloudinary.api.resources(
        type="upload", 
        max_results=500,
        expression=expression
    )
        
    for res in resources.get("resources", []):
        # The patient name is the folder name
        patient_name = res.get("folder", "Uncategorized")

        upload_date = datetime.strptime(
            res["created_at"], "%Y-%m-%dT%H:%M:%SZ"
        ).strftime('%b %d, %Y')

        original_filename = f"{res['public_id'].split('/')[-1]}.{res['format']}"

        file_obj = {
            'name': original_filename,
            'date': upload_date,
            'url': res['secure_url'],
            'public_id': res['public_id'],
            'is_pdf': res['resource_type'] == 'image' and res['format'] == 'pdf'
        }

        # Group files by patient
        if patient_name not in data:
            data[patient_name] = []
        data[patient_name].append(file_obj)

    # Sort files within each patient group by date
    for patient in data:
        data[patient].sort(key=lambda x: x['date'], reverse=True)

    return render_template("reports.html", data=data, search=search)

@app.route("/delete", methods=["POST"])
@login_required
def delete_file():
    """
    Deletes a specific report file from Cloudinary.
    Requires the user to be logged in.
    """
    public_id = request.form.get("public_id")
    if public_id:
        # Deleting requires the public_id
        cloudinary.uploader.destroy(public_id)
        flash(f"Report was deleted successfully.", "success")
    else:
        flash("Could not delete report: missing ID.", "error")
        
    return redirect(url_for('reports'))

if __name__ == "__main__":
    # The development server is not for production. A WSGI server like Gunicorn will run the app.
    app.run(debug=True, host='0.0.0.0')
