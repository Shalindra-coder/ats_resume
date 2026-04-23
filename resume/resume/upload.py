import os
import frappe
import json
from frappe import _


@frappe.whitelist()
def save_cv_to_pdf_upload(file_url, job_id, designation, action):
    frappe.msgprint(f"Saving CV to PDF Upload for Job ID: {job_id}, Action: {action}")
    if not file_url or not job_id:
        frappe.throw(_("File or Job Opening ID is missing."))

    # pdf_upload_name = frappe.db.get_value("PDF Upload", {"job_title": job_id}, "name")

    # if pdf_upload_name:
    #     doc = frappe.get_doc("PDF Upload", pdf_upload_name)
        
    #     # --- Duplicate Check: If file already exists in this PDF Upload ---
    #     for f in doc.files:
    #         if f.file_upload == file_url:
    #             frappe.throw(_("This resume has already been parsed for this job."))
    else:
        # Agar nahi hai toh naya record banayein
        doc = frappe.new_doc("PDF Upload")
        doc.job_title = job_id
        doc.designation = designation

    # 2. Child table 'files' mein entry add karein
    doc.append("files", {
        "file_upload": file_url
    })

    # 3. Save aur Commit
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # Action specific processing
    if action == "Parse":
        pass
    elif action == "Score":
        pass

    return doc.name



from resume.resume.doctype.pdf_upload.pdf_upload import (
    extract_text_from_any_file,
    _parse_text_threadsafe,
    _parse_pdf_threadsafe,
)

@frappe.whitelist()
def parse_cv_and_create_applicant_direct(file_url=None, file_urls=None, job_id=None, designation=None):

    if not job_id:
        frappe.throw(_("Job Opening ID is missing."))

    # --- STATUS CALCULATION (Dynamic) ---
    # Job Applicant ke status options nikalna
    status_options = frappe.get_meta("Job Applicant").get_options("status") or ""
    valid_statuses = [s.strip() for s in status_options.split("\n") if s.strip()]
    
    # Priority: "Open" -> "CV Submitted" -> First available option
    default_status = "Open"
    if "Open" in valid_statuses:
        default_status = "Open"
    elif "CV Submitted" in valid_statuses:
        default_status = "CV Submitted"
    elif valid_statuses:
        default_status = valid_statuses[0]

    #  Existing Emails for Duplicate Check
    existing_emails = frappe.db.get_all(
        "Job Applicant",
        filters={"job_title": job_id},
        fields=["email_id"]
    )
    existing_email_set = set(
        [d.email_id.lower().strip() for d in existing_emails if d.email_id]
    )

    duplicate_emails = []
    success_count = 0
    error_log = []

    # File handling
    if isinstance(file_urls, str):
        file_urls = json.loads(file_urls)

    if file_urls is None:
        file_urls = []

    if file_url:
        file_urls.append(file_url)

    if not file_urls:
        frappe.throw(_("No file(s) provided."))

    #  Loop
    for f_url in file_urls:
        try:
            current_file_url = f_url
            site_url = frappe.utils.get_url()

            if current_file_url.startswith(site_url):
                current_file_url = current_file_url.split(site_url, 1)[1]

            if not current_file_url.startswith("/"):
                current_file_url = "/" + current_file_url

            # File path resolution
            file_path = None
            file_list = frappe.get_all("File", filters={"file_url": current_file_url}, limit=1)

            if file_list:
                file_doc = frappe.get_doc("File", file_list[0].name)
                file_path = file_doc.get_full_path()

            if not file_path or not os.path.exists(file_path):
                path_parts = current_file_url.lstrip("/").split("/")
                file_path = os.path.abspath(frappe.get_site_path(*path_parts))

            if not os.path.exists(file_path):
                error_log.append(f"File not found: {f_url}")
                continue

            # API + Prompt
            api_key = frappe.conf.get("gemini_api_key")
            prompt_path = frappe.get_app_path(
                "resume", "resume", "doctype", "pdf_upload", "parse_only_prompt.txt"
            )

            with open(prompt_path, "r") as f:
                prompt_template = f.read()

            ext = os.path.splitext(file_path)[1].lower()
            job_desc = frappe.db.get_value("Job Opening", job_id, "description")

            #  AI Parsing
            if ext == ".pdf":
                text = extract_text_from_any_file(file_path)
                if text:
                    applicant_data = _parse_text_threadsafe(api_key, prompt_template, text, job_id, job_desc)
                else:
                    applicant_data = _parse_pdf_threadsafe(api_key, prompt_template, file_path, job_id, job_desc)
            else:
                text = extract_text_from_any_file(file_path)
                applicant_data = _parse_text_threadsafe(api_key, prompt_template, text, job_id, job_desc)

            email = applicant_data.get("email_id", "").lower().strip()
            name = applicant_data.get("applicant_name", "Unknown")

            if not email:
                error_log.append(f"Email not found in file: {os.path.basename(f_url)}")
                continue

            # DUPLICATE CHECK
            if email in existing_email_set:
                duplicate_emails.append(f"{name} ({email})")
                continue

            #  Create Applicant
            applicant = frappe.get_doc({
                "doctype": "Job Applicant",
                "applicant_name": name,
                "email_id": email,
                "phone_number": applicant_data.get("phone_number", ""),
                "custom_phone_number_2": applicant_data.get("custom_phone_number_2", ""), # Extra field from your second snippet
                "resume_attachment": current_file_url,
                "status": default_status, # Ab yahan dynamic status aayega
                "job_title": job_id,
                "designation": designation,
            })

            applicant.insert(ignore_permissions=True)
            frappe.db.commit()

            existing_email_set.add(email)
            success_count += 1

        except Exception as e:
            error_log.append(f"{os.path.basename(f_url)}: {str(e)}")

    #  FINAL MESSAGE
    message = ""
    if success_count:
        message += f" {success_count} Applicant(s) Created Successfully\n\n"

    if duplicate_emails:
        message += " Duplicate Resumes Found (Skipped):\n"
        message += "\n".join(duplicate_emails) + "\n\n"

    if error_log:
        message += " Errors:\n"
        message += "\n".join(error_log)

    if message:
        frappe.msgprint(message, title="CV Processing Result")

    return {"status": "completed", "success_count": success_count}


