"""
Web application for PDF to LaTeX converter.

Run with: python app.py
Then open http://localhost:5000 in your browser.
"""

import os
import uuid
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import threading
import queue

from converter import PDFToLatexConverter, ConversionResult

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = Path("uploads")
OUTPUT_FOLDER = Path("output")
ALLOWED_EXTENSIONS = {"pdf"}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

# Create directories
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Store conversion jobs
jobs = {}


def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def conversion_worker(job_id: str, pdf_path: str, output_dir: str, backend: str, output_format: str):
    """Worker function to process conversion in background."""
    try:
        converter = PDFToLatexConverter(backend=backend)
        result = converter.convert(pdf_path, output_dir, output_format)
        jobs[job_id]["result"] = result
        jobs[job_id]["status"] = "completed"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


@app.route("/api/convert", methods=["POST"])
def convert():
    """Handle PDF upload and conversion."""
    # Check if file was uploaded
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    
    # Get options
    backend = request.form.get("backend", "nougat")
    output_format = request.form.get("format", "markdown")
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    job_id = str(uuid.uuid4())
    upload_path = UPLOAD_FOLDER / f"{job_id}_{filename}"
    file.save(upload_path)
    
    # Create output directory
    output_dir = OUTPUT_FOLDER / job_id
    output_dir.mkdir(exist_ok=True)
    
    # Initialize job
    jobs[job_id] = {
        "status": "processing",
        "filename": filename,
        "backend": backend,
        "output_format": output_format
    }
    
    # Start conversion in background
    thread = threading.Thread(
        target=conversion_worker,
        args=(job_id, str(upload_path), str(output_dir), backend, output_format)
    )
    thread.start()
    
    return jsonify({
        "job_id": job_id,
        "status": "processing"
    })


@app.route("/api/status/<job_id>")
def status(job_id):
    """Check the status of a conversion job."""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    
    response = {
        "status": job["status"],
        "filename": job.get("filename"),
    }
    
    if job["status"] == "completed":
        result: ConversionResult = job["result"]
        response["success"] = result.success
        response["pages_processed"] = result.pages_processed
        response["output_format"] = result.output_format
        
        if result.success:
            # Return the content
            response["content"] = result.content
            response["content_length"] = len(result.content)
        else:
            response["error"] = result.error_message
    
    elif job["status"] == "failed":
        response["error"] = job.get("error")
    
    return jsonify(response)


@app.route("/api/download/<job_id>")
def download(job_id):
    """Download the converted file."""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        return jsonify({"error": "Job not completed"}), 400
    
    result: ConversionResult = job["result"]
    if not result.success:
        return jsonify({"error": "Conversion failed"}), 400
    
    output_dir = OUTPUT_FOLDER / job_id
    filename = Path(job["filename"]).stem
    extension = "tex" if result.output_format == "latex" else "mmd"
    output_file = output_dir / f"{filename}.{extension}"
    
    if output_file.exists():
        return send_file(
            output_file,
            as_attachment=True,
            download_name=f"{filename}.{extension}"
        )
    
    return jsonify({"error": "Output file not found"}), 404


@app.route("/api/backends")
def backends():
    """Return information about available backends."""
    backend_info = {
        "nougat": {
            "name": "Nougat",
            "description": "Meta's model for scientific papers with math and tables",
            "best_for": "Academic papers, complex layouts",
            "installed": False
        },
        "texify": {
            "name": "Texify",
            "description": "Excellent for math-heavy documents",
            "best_for": "Math equations, mixed content",
            "installed": False
        },
        "pix2tex": {
            "name": "LaTeX-OCR (pix2tex)",
            "description": "Specialized for math equations",
            "best_for": "Single equations, math images",
            "installed": False
        }
    }
    
    for backend in backend_info:
        try:
            __import__(backend)
            backend_info[backend]["installed"] = True
        except ImportError:
            pass
    
    return jsonify(backend_info)


@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files."""
    return send_from_directory("static", filename)


if __name__ == "__main__":
    print("=" * 50)
    print("PDF to LaTeX Converter")
    print("=" * 50)
    print("\nStarting web server...")
    print("Open http://localhost:5000 in your browser\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
