# apps/resume/resume/api/upload_and_process.py
import frappe
import os
import uuid
from pdfminer.high_level import extract_text
from resume.resume.doctype.pdf_upload.pdf_upload import extract_text_with_ocr, parse_with_gemini

@frappe.whitelist()
def upload_and_process(job_opening=None):
    """
    Upload files (multipart/form-data 'files') and create Job Applicant records.
    Expects:
      - files: multipart form files (one or many)
      - job_opening: name/ID of the Job Opening (optional)
    Returns:
      JSON with message of created count or raises a frappe exception on fatal errors.
    """
    # Allow guest calls if configured; ensure CSRF won't block guest uploads
    # NOTE: this flag only affects the current request thread
    try:
        frappe.local.flags.ignore_csrf = True
    except Exception:
        # If frappe.local not available for some reason, continue — not fatal
        pass

    # If job_opening not provided in args, check form_dict (multipart form)
    if not job_opening:
        job_opening = frappe.form_dict.get("job_opening")

    # Try to resolve job title/description for context (optional)
    job_title = None
    job_description = None
    if job_opening:
        try:
            job_doc = frappe.get_doc("Job Opening", job_opening)
            job_title = job_doc.get("job_title")
            job_description = job_doc.get("description")
        except Exception:
            # Non-fatal: continue without job context
            frappe.log_error(message=f"Could not load Job Opening {job_opening}", title="upload_and_process: Job Opening lookup failed")

    try:
        # Get uploaded files from the request
        files = []
        try:
            files = frappe.request.files.getlist("files")
        except Exception:
            # In some setups getlist may not exist; fallback to single file under 'files'
            f = frappe.request.files.get("files")
            if f:
                files = [f]

        if not files:
            frappe.throw("No files uploaded. Please upload at least one PDF as 'files' field.")

        created = 0

        for file_storage in files:
            # file_storage is a Werkzeug FileStorage-like object
            filename_orig = getattr(file_storage, "filename", None) or "uploaded_file"
            filename = f"{uuid.uuid4().hex}_{filename_orig}"
            # ensure destination directory
            dest_dir = frappe.get_site_path("private", "files")
            os.makedirs(dest_dir, exist_ok=True)
            file_path = os.path.join(dest_dir, filename)

            # Save file to private/files
            try:
                with open(file_path, "wb") as f:
                    # file_storage.stream is typically available; fallback to read()
                    try:
                        f.write(file_storage.stream.read())
                    except Exception:
                        file_storage.seek(0)
                        f.write(file_storage.read())
            except Exception as e:
                frappe.log_error(message=f"Failed to save uploaded file {filename_orig}: {e}", title="upload_and_process: file save error")
                # skip this file and continue with others
                continue

            # Build a file URL that can be stored on the Doc
            file_url = f"/private/files/{filename}"

            # Extract text from PDF (pdfminer) and fallback to OCR if empty
            try:
                text = extract_text(file_path)
                if not text or not text.strip():
                    # do OCR fallback
                    text = extract_text_with_ocr(file_path)
            except Exception as e:
                frappe.log_error(message=f"Text extraction failed for {filename}: {e}", title="upload_and_process: extraction failed")
                # skip file on extraction failure
                continue

            # Parse with Gemini (AI)
            try:
                applicant_data = parse_with_gemini(text, job_title, job_description)
            except Exception as e:
                frappe.log_error(message=f"Gemini parsing failed for {filename}: {e}", title="upload_and_process: parsing failed")
                # skip file if parsing fails
                continue

            # Normalize keys from AI to expected fields
            # Accept either 'email' or 'email_id'; phone may be 'phone' or 'phone_number'
            if "email_id" in applicant_data and "email" not in applicant_data:
                applicant_data["email"] = applicant_data["email_id"]
            if "email" in applicant_data and "email_id" not in applicant_data:
                applicant_data["email_id"] = applicant_data["email"]

            if "phone_number" in applicant_data and "phone" not in applicant_data:
                applicant_data["phone"] = applicant_data["phone_number"]
            if "phone" in applicant_data and "phone_number" not in applicant_data:
                applicant_data["phone_number"] = applicant_data["phone"]

            # Basic validation
            applicant_name = applicant_data.get("applicant_name") or applicant_data.get("name") or applicant_data.get("full_name")
            email_value = applicant_data.get("email") or applicant_data.get("email_id")

            if not applicant_name or not email_value:
                frappe.log_error(message=f"Missing required applicant info (name/email) for {filename}: parsed data keys: {list(applicant_data.keys())}", title="upload_and_process: missing data")
                # skip creating applicant
                continue

            # Prevent duplicates for same job (check by email + job)
            try:
                exists_filters = {"email_id": email_value}
                if job_opening:
                    exists_filters["job_title"] = job_opening
                if frappe.db.exists("Job Applicant", exists_filters):
                    frappe.log_error(message=f"Duplicate applicant for email {email_value} and job {job_opening}", title="upload_and_process: duplicate")
                    continue
            except Exception as e:
                # If exists check fails, log and continue (do not block)
                frappe.log_error(message=f"Error checking duplicates for {email_value}: {e}", title="upload_and_process: duplicate check failed")

            # Build Job Applicant doc
            try:
                applicant_doc = {
                    "doctype": "Job Applicant",
                    "applicant_name": applicant_name,
                    "email_id": email_value,
                    "resume_attachment": file_url,
                    "status": "Open",
                    # phone fields
                    "phone_number": applicant_data.get("phone_number") or applicant_data.get("phone") or "",
                    # rating/score/fit_level if present
                    "applicant_rating": applicant_data.get("applicant_rating") or applicant_data.get("rating") or 0,
                    "score": applicant_data.get("score"),
                    "fit_level": applicant_data.get("fit_level"),
                    "justification_by_ai": applicant_data.get("justification_by_ai", "")
                }

                if job_opening:
                    applicant_doc["job_title"] = job_opening

                # Insert applicant
                applicant = frappe.get_doc(applicant_doc)
                applicant.insert(ignore_permissions=True)
                created += 1
                frappe.logger().info(f"Created Job Applicant {email_value} from {filename}")
            except Exception as e:
                frappe.log_error(message=f"Failed to insert Job Applicant for {filename} ({email_value}): {e}", title="upload_and_process: insert failed")
                # continue processing other files
                continue

        return {"message": f"{created} Job Applicant(s) created."}

    except Exception as e:
        # Critical failure for the endpoint
        frappe.log_error(message=f"Resume upload failed: {e}", title="upload_and_process: critical")
        frappe.throw("Resume upload failed. See error logs.")
