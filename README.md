# Medical Patient Reports Web Application

This is a simple Flask web application for uploading and viewing medical patient reports. It allows for uploading files for specific patients and provides a password-protected area for doctors to view, search, and manage these reports.

## Features

- **File Upload**: Upload patient reports (PDF, PNG, JPG, etc.).
- **Patient Organization**: Files are automatically organized into folders by patient name.
- **Doctor Dashboard**: A secure, login-protected dashboard for doctors.
- **Search**: Search for patients within the dashboard.
- **File Preview**: Preview images and PDFs directly in the browser.
- **File Deletion**: Doctors can delete reports.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd patient-report-site
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the application:**
    ```bash
    flask run
    ```
