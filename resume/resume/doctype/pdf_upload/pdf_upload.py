


import frappe
import os
import json
import mimetypes
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pdfminer.high_level import extract_text
from frappe.model.document import Document
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import docx  # For .docx files
import google.generativeai as genai

# Max concurrent Gemini API calls - keep low to avoid rate limits (429)
PARALLEL_WORKERS = 2
GEMINI_RETRY_ATTEMPTS = 4
GEMINI_RETRY_BASE_DELAY = 3  # seconds

class PDFUpload(Document):
    pass

@frappe.whitelist()
def process_pdfs(docname):
    """Enqueues the processing job for all types of files."""
    frappe.enqueue("resume.resume.doctype.pdf_upload.pdf_upload.process_files_background", queue="long", docname=docname)
    frappe.msgprint("File processing has been queued in the background.")

# --- AI Logic (UNCHANGED as per request) ---
@frappe.whitelist()
def list_available_gemini_models():
    """List available Gemini models for debugging."""
    try:
        api_key = frappe.conf.get("gemini_api_key")
        if not api_key:
            return {"error": "Gemini API key missing in site_config.json"}
        
        genai.configure(api_key=api_key)
        models = genai.list_models()
        available_models = []
        model_details = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name
                model_id = model_name.replace('models/', '')
                available_models.append(model_id)
                model_details.append({
                    "full_name": model_name,
                    "model_id": model_id,
                    "display_name": getattr(model, 'display_name', 'N/A'),
                    "supported_methods": list(model.supported_generation_methods)
                })
        
        frappe.logger().info(f"Available Gemini models: {available_models}")
        return {"available_models": available_models, "model_details": model_details}
    except Exception as e:
        frappe.logger().error(f"Error listing Gemini models: {str(e)}")
        return {"error": str(e)}

def parse_with_gemini(text, job_title=None, job_description=None):
    """AI Logic: Send resume text to Gemini model and return structured JSON."""
    # (No changes made to this function as requested)
    try:
        api_key = frappe.conf.get("gemini_api_key")
        if not api_key:
            raise Exception("Gemini API key missing in site_config.json")

        genai.configure(api_key=api_key)
        prompt_path = frappe.get_app_path("resume", "resume", "doctype", "pdf_upload", "resume_prompt.txt")
        with open(prompt_path, "r") as f:
            prompt_template = f.read()

        prompt = prompt_template.replace("{{RESUME_TEXT}}", text)
        prompt = prompt.replace("{{JOB_TITLE}}", job_title or "N/A")
        prompt = prompt.replace("{{JOB_DESCRIPTION}}", job_description or "N/A")

        model_names = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]  # flash first for speed
        last_error = None
        skipped_models = []
        
        def try_models(models_to_try):
            nonlocal last_error
            for model_name in models_to_try:
                try:
                    frappe.logger().info(f"Gemini model: {model_name}")
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    cleaned = response.text.strip()
                    if cleaned.startswith("```json"): cleaned = cleaned[7:]
                    if cleaned.endswith("```"): cleaned = cleaned[:-3]
                    return json.loads(cleaned.strip())
                except Exception as e:
                    if "Computer Use tool" in str(e):
                        skipped_models.append(model_name)
                        continue
                    last_error = e
                    continue
            return None

        result = try_models(model_names)
        if result: return result
        
        # Dynamic fallback
        models = genai.list_models()
        dynamic_models = [m.name.replace('models/', '') for m in models 
                          if 'generateContent' in m.supported_generation_methods 
                          and m.name.replace('models/', '') not in model_names]
        return try_models(dynamic_models) or (lambda: exec('raise last_error'))()
    except Exception as e:
        frappe.logger().error(f"Gemini parsing failed: {e}")
        raise

# --- Text Extraction Logic (Enhanced for all formats) ---

def extract_text_from_any_file(file_path):
    """Detects file type and extracts text accordingly."""
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    frappe.logger().info(f"Starting extraction for file: {file_path} with extension: {ext}")

    if ext == ".pdf":
        text = extract_text(file_path)
        if not text.strip():
            # Image-based PDF: return None - caller will use parse_with_gemini_file (direct PDF to Gemini)
            # This bypasses OCR/poppler which often fails and is slow
            return None
    
    elif ext == ".docx":
        doc = docx.Document(file_path)
        parts = [para.text for para in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text.strip() for cell in row.cells))
        text = "\n".join(parts)
    
    elif ext in [".jpg", ".jpeg", ".png"]:
        text = pytesseract.image_to_string(Image.open(file_path))
    
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    
    else:
        frappe.logger().warning(f"Unsupported file format: {ext}")
        return None

    return text.strip()

def extract_text_with_ocr(file_path):
    """OCR for Scanned PDFs."""
    try:
        images = convert_from_path(file_path)
        return "\n".join([pytesseract.image_to_string(img) for img in images])
    except Exception as e:
        frappe.logger().error(f"OCR Error: {str(e)}")
        return ""

import base64
def parse_with_gemini_file(file_path, job_title=None, job_description=None):
    """Send PDF directly to Gemini - bypasses OCR, works for image-based PDFs. Faster."""
    api_key = frappe.conf.get("gemini_api_key")
    if not api_key:
        raise Exception("Gemini API key missing in site_config.json")

    genai.configure(api_key=api_key)
    prompt_path = frappe.get_app_path("resume", "resume", "doctype", "pdf_upload", "resume_prompt.txt")
    with open(prompt_path, "r") as f:
        prompt_template = f.read()

    prompt = prompt_template.replace("{{RESUME_TEXT}}", "Resume attached as PDF.")
    prompt = prompt.replace("{{JOB_TITLE}}", job_title or "N/A")
    prompt = prompt.replace("{{JOB_DESCRIPTION}}", job_description or "N/A")

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    model_names = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]  # flash first for speed
    last_error = None
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                [
                    {"mime_type": "application/pdf", "data": pdf_bytes},
                    prompt
                ]
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            last_error = e
            frappe.logger().warning(f"Gemini {model_name} failed for PDF: {e}")
            continue
    raise last_error

# --- Background Job (Parallel Processing) ---

def _is_retryable_error(exc):
    """Check if error is rate limit or transient (worth retrying)."""
    msg = str(exc).lower()
    return any(x in msg for x in ["429", "resource_exhausted", "rate limit", "quota", "503", "overloaded"])

def _call_gemini_with_retry(call_fn):
    """Execute Gemini API call with exponential backoff on rate limits."""
    last_error = None
    for attempt in range(GEMINI_RETRY_ATTEMPTS):
        try:
            return call_fn()
        except Exception as e:
            last_error = e
            if attempt < GEMINI_RETRY_ATTEMPTS - 1 and _is_retryable_error(e):
                delay = GEMINI_RETRY_BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
    raise last_error

def _parse_text_threadsafe(api_key, prompt_template, text, job_title, job_desc):
    """Thread-safe: parse text with Gemini. Retries on rate limit."""
    genai.configure(api_key=api_key)
    prompt = prompt_template.replace("{{RESUME_TEXT}}", text)
    prompt = prompt.replace("{{JOB_TITLE}}", job_title or "N/A")
    prompt = prompt.replace("{{JOB_DESCRIPTION}}", job_desc or "N/A")
    last_error = None
    for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]:
        try:
            def _call(m=model_name, p=prompt):
                model = genai.GenerativeModel(m)
                response = model.generate_content(p)
                cleaned = response.text.strip()
                if cleaned.startswith("```json"): cleaned = cleaned[7:]
                if cleaned.endswith("```"): cleaned = cleaned[:-3]
                return json.loads(cleaned.strip())
            return _call_gemini_with_retry(lambda: _call())
        except Exception as e:
            last_error = e
            continue
    raise last_error or Exception("All Gemini models failed")

def _parse_pdf_threadsafe(api_key, prompt_template, file_path, job_title, job_desc):
    """Thread-safe: send PDF to Gemini. Retries on rate limit."""
    genai.configure(api_key=api_key)
    prompt = prompt_template.replace("{{RESUME_TEXT}}", "Resume attached as PDF.")
    prompt = prompt.replace("{{JOB_TITLE}}", job_title or "N/A")
    prompt = prompt.replace("{{JOB_DESCRIPTION}}", job_desc or "N/A")
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
    last_error = None
    for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]:
        try:
            def _call(m=model_name, p=prompt, b=pdf_bytes):
                model = genai.GenerativeModel(m)
                response = model.generate_content([{"mime_type": "application/pdf", "data": b}, p])
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            return _call_gemini_with_retry(lambda: _call())
        except Exception as e:
            last_error = e
            continue
    raise last_error or Exception("All Gemini models failed for PDF")

def _extract_text(file_path, ext):
    """Extract text from file. No frappe logging."""
    if ext == ".pdf":
        text = extract_text(file_path)
        return text.strip() if text else None
    elif ext == ".docx":
        doc = docx.Document(file_path)
        parts = [para.text for para in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text.strip() for cell in row.cells))
        return "\n".join(parts)
    elif ext in [".jpg", ".jpeg", ".png"]:
        return pytesseract.image_to_string(Image.open(file_path))
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return None

def _extract_and_parse_file(args):
    """Runs in thread. Uses pre-loaded api_key + prompt_template. No frappe calls."""
    file_path, file_url, job_title, job_desc, ext, api_key, prompt_template = args
    try:
        if ext == ".pdf":
            text = _extract_text(file_path, ext)
            if text:
                applicant_data = _parse_text_threadsafe(api_key, prompt_template, text, job_title, job_desc)
            else:
                applicant_data = _parse_pdf_threadsafe(api_key, prompt_template, file_path, job_title, job_desc)
        else:
            text = _extract_text(file_path, ext)
            if not text:
                return (file_url, None, f"Could not extract text from {file_url}")
            applicant_data = _parse_text_threadsafe(api_key, prompt_template, text, job_title, job_desc)
        return (file_url, applicant_data, None)
    except Exception as e:
        return (file_url, None, str(e))



def process_files_background(docname):
    """Processes uploaded files in parallel - multiple resumes parsed concurrently for speed."""
    import time
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed

    t_start = time.perf_counter()

    try:
        doc = frappe.get_doc("PDF Upload", docname)
        if not doc.get("files"):
            frappe.logger().warning(f"PDF Upload {docname}: No files found.")
            return

        job_desc = frappe.db.get_value("Job Opening", doc.job_title, "description") if doc.job_title else None
        job_title = doc.job_title

        #  STEP 1: Get all existing emails once (FAST)
        existing_emails = frappe.db.get_all("Job Applicant", fields=["email_id"])
        existing_email_set = set([d.email_id for d in existing_emails if d.email_id])

        print(" Existing Emails Loaded:", existing_email_set)

        duplicate_emails = []

        # Pre-load for threads
        api_key = frappe.conf.get("gemini_api_key")
        if not api_key:
            frappe.logger().error("Gemini API key missing in site_config.json")
            return

        prompt_path = frappe.get_app_path("resume", "resume", "doctype", "pdf_upload", "resume_prompt.txt")
        with open(prompt_path, "r") as f:
            prompt_template = f.read()

        # 1. Resolve file paths
        t_path_start = time.perf_counter()
        tasks = []

        for file_entry in doc.get("files"):
            file_url = file_entry.get("file_upload")
            if not file_url:
                continue

            site_url = frappe.utils.get_url()
            if file_url.startswith(site_url):
                file_url = file_url.split(site_url, 1)[1]

            if not file_url.startswith("/"):
                file_url = "/" + file_url

            file_path = None
            file_list = frappe.get_all("File", filters={"file_url": file_url}, limit=1)

            if file_list:
                try:
                    file_doc = frappe.get_doc("File", file_list[0].name)
                    file_path = file_doc.get_full_path()
                except Exception:
                    pass

            if not file_path or not os.path.exists(file_path):
                path_parts = file_url.lstrip("/").split("/") if file_url.startswith("/private") else ["public"] + file_url.lstrip("/").split("/")
                file_path = os.path.abspath(frappe.get_site_path(*path_parts))

            if not os.path.exists(file_path):
                frappe.logger().error(f"File not found on server: {file_path}")
                continue

            ext = os.path.splitext(file_path)[1].lower()
            tasks.append((file_path, file_url, job_title, job_desc, ext, api_key, prompt_template))

        if not tasks:
            return

        t_path_elapsed = time.perf_counter() - t_path_start
        frappe.logger().info(f"Path resolved in {t_path_elapsed:.2f}s for {len(tasks)} files")

        # 2. Parse files
        t_parse_start = time.perf_counter()
        workers = min(PARALLEL_WORKERS, len(tasks))
        results = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for i, t in enumerate(tasks):
                if i > 0:
                    time.sleep(2)
                futures[executor.submit(_extract_and_parse_file, t)] = t

            for future in as_completed(futures):
                file_url, applicant_data, error_msg = future.result()

                if error_msg:
                    frappe.logger().error(f"Parsing failed for {file_url}: {error_msg}")
                elif applicant_data:
                    results.append((file_url, applicant_data))

        t_parse_elapsed = time.perf_counter() - t_parse_start
        frappe.logger().info(f"Parsing done in {t_parse_elapsed:.2f}s")

        # 3. Create Job Applicants
        t_db_start = time.perf_counter()

        status_options = frappe.get_meta("Job Applicant").get_options("status") or ""
        valid_statuses = [s.strip() for s in status_options.split("\n") if s.strip()]
        default_status = "CV Submitted" if "CV Submitted" in valid_statuses else (valid_statuses[0] if valid_statuses else "Open")

        for file_url, applicant_data in results:
            email = applicant_data.get("email_id")

            if not email or not applicant_data.get("applicant_name"):
                frappe.logger().warning(f"Missing Name/Email in AI response for {file_url}")
                continue

            if email in existing_email_set:
                print(f" Duplicate Resumes Found: {email}")
                frappe.logger().info(f"Duplicate: {email}")
                duplicate_emails.append(email)
                continue

            try:
                new_applicant = frappe.get_doc({
                    "doctype": "Job Applicant",
                    "applicant_name": applicant_data.get("applicant_name"),
                    "email_id": email,
                    "phone_number": applicant_data.get("phone_number"),
                    "custom_phone_number_2": applicant_data.get("custom_phone_number_2", ""),
                    "resume_attachment": file_url,
                    "status": default_status,
                    "job_title": doc.job_title,
                    "designation": doc.designation,
                    "applicant_rating": applicant_data.get("applicant_rating"),
                    "score": applicant_data.get("score"),
                    "fit_level": applicant_data.get("fit_level"),
                    "justification_by_ai": applicant_data.get("justification_by_ai"),
                    "custom_yes": 1
                })

                new_applicant.insert(ignore_permissions=True)

                existing_email_set.add(email)

                frappe.logger().info(f"Created Applicant: {new_applicant.name}")

            except Exception as e:
                frappe.logger().error(f"DB insert failed for {email}: {str(e)}")

        t_db_elapsed = time.perf_counter() - t_db_start


        if duplicate_emails:
            message = (
                f" Duplicate Resumes: {len(duplicate_emails)}<br><br>"
                + "<br>".join(duplicate_emails)
            )

            frappe.msgprint(message)

            #  Background job ke liye (important)
            frappe.publish_realtime("msgprint", {"message": message})

        else:
            frappe.msgprint(" No Duplicate Resumes Found")

        t_total = time.perf_counter() - t_start
        frappe.logger().info(
            f"Total Time: {t_total:.2f}s | Parse: {t_parse_elapsed:.2f}s | DB: {t_db_elapsed:.2f}s"
        )

    except Exception as e:
        frappe.logger().error(f"Critical error in background job {docname}: {str(e)}")