import os
import frappe
import json
from frappe import _
from datetime import datetime

@frappe.whitelist()
def save_cv_to_pdf_upload(file_url, job_id, designation, action):
    frappe.msgprint(
        f"Saving CV to PDF Upload for Job ID: {job_id}, Action: {action}"
    )

    if not file_url or not job_id:
        frappe.throw(_("File or Job Opening ID is missing."))

    # Create new PDF Upload document
    doc = frappe.new_doc("PDF Upload")
    doc.job_title = job_id
    doc.designation = designation

    # Add file to child table
    doc.append(
        "files",
        {
            "file_upload": file_url
        }
    )

    # Save and commit
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


def _is_valid_attachment_name(name):
    """Frappe rejects falsy ints (e.g. 0) and non str/int types."""

    if name is None or name == "" or name is False:
        return False

    if isinstance(name, bool):
        return False

    if isinstance(name, int) and name == 0:
        return False

    if isinstance(name, float) and name == 0:
        return False

    if isinstance(name, str):
        stripped = name.strip()

        if not stripped or stripped in (
            "0",
            "undefined",
            "null",
            "None",
        ):
            return False

        return True

    return isinstance(name, int)


def _clear_invalid_upload_attachment_fields():
    """Remove bad doctype/docname from upload_file requests."""

    doctype = frappe.form_dict.get("doctype")
    docname = frappe.form_dict.get("docname")

    if doctype and not _is_valid_attachment_name(docname):
        for key in ("doctype", "docname", "fieldname"):
            frappe.form_dict.pop(key, None)


def clear_invalid_upload_attachment_on_request():
    if frappe.form_dict.get("cmd") == "upload_file":
        _clear_invalid_upload_attachment_fields()


def sanitize_cv_file_attachment(doc, method=None):
    """Drop invalid attached_to references."""

    if not doc.attached_to_doctype:
        return

    if not _is_valid_attachment_name(doc.attached_to_name):
        doc.attached_to_doctype = None
        doc.attached_to_name = None
        doc.attached_to_field = None


@frappe.whitelist(allow_guest=True)
def upload_file_safe():
    """Wrap frappe.handler.upload_file and strip invalid attachment targets."""

    if frappe.form_dict.get("method") == "resume.resume.upload.upload_cv_for_parsing":

        for key in ("doctype", "docname", "fieldname", "method"):
            frappe.form_dict.pop(key, None)

        return upload_cv_for_parsing()

    _clear_invalid_upload_attachment_fields()

    from frappe.handler import upload_file

    return upload_file()


@frappe.whitelist(allow_guest=True)
def upload_cv_for_parsing():
    """Upload a CV to Home without attaching to Job Opening."""

    from mimetypes import guess_type

    from frappe.handler import ALLOWED_MIMETYPES
    from frappe.utils import cint
    from frappe.utils.image import optimize_image

    ignore_permissions = False
    user = None

    if frappe.session.user == "Guest":

        if not frappe.get_system_settings(
            "allow_guests_to_upload_files"
        ):
            raise frappe.PermissionError

        ignore_permissions = True

    else:
        user = frappe.get_doc("User", frappe.session.user)

    files = frappe.request.files

    is_private = cint(
        frappe.form_dict.get("is_private", 1)
    )

    folder = frappe.form_dict.get("folder") or "Home"

    file_url = frappe.form_dict.get("file_url")

    filename = frappe.form_dict.get("file_name")

    optimize = frappe.form_dict.get("optimize")

    content = getattr(
        frappe.local,
        "uploaded_file",
        None
    )

    # Library file
    if library_file := frappe.form_dict.get("library_file_name"):

        frappe.has_permission(
            "File",
            doc=library_file,
            throw=True
        )

        lib = frappe.get_value(
            "File",
            library_file,
            [
                "is_private",
                "file_url",
                "file_name",
            ],
            as_dict=True,
        )

        is_private = lib.is_private
        file_url = lib.file_url
        filename = lib.file_name

    # Uploaded file
    if not content and files and "file" in files:

        upload = files["file"]

        content = upload.stream.read()

        filename = filename or upload.filename

    elif not filename:

        filename = getattr(
            frappe.local,
            "uploaded_filename",
            None
        )

    if (
        not content
        and not file_url
        and not frappe.form_dict.get("library_file_name")
    ):
        frappe.throw(_("Please attach a file."))

    # Optimize image
    if content and files and "file" in files:

        upload = files["file"]

        filename = filename or upload.filename

        content_type = guess_type(filename)[0]

        if optimize and content_type and content_type.startswith("image/"):

            args = {
                "content": content,
                "content_type": content_type,
            }

            if frappe.form_dict.get("max_width"):
                args["max_width"] = int(
                    frappe.form_dict.max_width
                )

            if frappe.form_dict.get("max_height"):
                args["max_height"] = int(
                    frappe.form_dict.max_height
                )

            content = optimize_image(**args)

    # Permission / file type validation
    if content is not None and (
        frappe.session.user == "Guest"
        or (user and not user.has_desk_access())
    ):

        filetype = guess_type(filename)[0]

        if filetype not in ALLOWED_MIMETYPES:

            frappe.throw(
                _(
                    "You can only upload JPG, PNG, PDF, TXT, CSV "
                    "or Microsoft documents."
                )
            )

    # Create File document
    file_doc = frappe.get_doc(
        {
            "doctype": "File",
            "folder": folder,
            "file_name": filename,
            "file_url": file_url,
            "is_private": is_private,
            "content": content,
        }
    )

    # CV files should not be attached automatically
    file_doc.attached_to_doctype = None
    file_doc.attached_to_name = None
    file_doc.attached_to_field = None

    sanitize_cv_file_attachment(file_doc)

    return file_doc.save(
        ignore_permissions=ignore_permissions
    )


def _safe_parse_text(
    api_key,
    prompt_template,
    text,
    job_id,
    job_desc
):
    """
    Safely parse extracted CV text.
    Always return dictionary.
    """

    if not text:
        return {}

    try:

        data = _parse_text_threadsafe(
            api_key,
            prompt_template,
            text,
            job_id,
            job_desc,
        )

        if isinstance(data, dict):
            return data

        return {}

    except Exception:

        frappe.log_error(
            title="CV Text Parsing Error",
            message=frappe.get_traceback()
        )

        return {}


def _safe_parse_pdf(
    api_key,
    prompt_template,
    file_path,
    job_id,
    job_desc
):
    """
    Safely parse file directly.

    This fallback is used when normal text extraction
    does not provide an email ID.
    """

    try:

        data = _parse_pdf_threadsafe(
            api_key,
            prompt_template,
            file_path,
            job_id,
            job_desc,
        )

        if isinstance(data, dict):
            return data

        return {}

    except Exception:

        frappe.log_error(
            title="CV Direct File Parsing Error",
            message=frappe.get_traceback()
        )

        return {}


def _merge_applicant_data(primary_data, fallback_data):
    """
    Merge two parser results.

    Existing values from primary_data are retained.
    Missing values are taken from fallback_data.
    """

    primary_data = (
        primary_data
        if isinstance(primary_data, dict)
        else {}
    )

    fallback_data = (
        fallback_data
        if isinstance(fallback_data, dict)
        else {}
    )

    merged_data = dict(primary_data)

    for key, value in fallback_data.items():

        current_value = merged_data.get(key)

        if (
            current_value is None
            or str(current_value).strip() == ""
        ):

            if value is not None and str(value).strip() != "":
                merged_data[key] = value

    return merged_data


def _normalize_email(email):
    """
    Safely normalize email.

    Prevents:
    'NoneType' object has no attribute 'lower'
    """

    if email is None:
        return ""

    if not isinstance(email, str):
        email = str(email)

    return email.strip().lower()


@frappe.whitelist()
def parse_cv_and_create_applicant_direct(
    file_url=None,
    file_urls=None,
    job_id=None,
    designation=None
):

    if not job_id:
        frappe.throw(
            _("Job Opening ID is missing.")
        )

    # STATUS CALCULATION

    status_options = (
        frappe.get_meta("Job Applicant")
        .get_options("status")
        or ""
    )

    valid_statuses = [
        s.strip()
        for s in status_options.split("\n")
        if s.strip()
    ]

    # Priority:
    # Open -> CV Submitted -> First available status

    default_status = "Open"

    if "Open" in valid_statuses:

        default_status = "Open"

    elif "CV Submitted" in valid_statuses:

        default_status = "CV Submitted"

    elif valid_statuses:

        default_status = valid_statuses[0]

    # EXISTING EMAILS

    existing_emails = frappe.db.get_all(
        "Job Applicant",
        filters={
            "job_title": job_id
        },
        fields=[
            "email_id"
        ]
    )

    existing_email_set = set()

    for d in existing_emails:

        email = _normalize_email(
            d.get("email_id")
        )

        if email:
            existing_email_set.add(email)

    # VARIABLES

    duplicate_emails = []

    success_count = 0

    error_log = []

    today_date = datetime.now().strftime(
        "%B %Y"
    )

    # FILE HANDLING

    if isinstance(file_urls, str):

        try:

            file_urls = json.loads(file_urls)

        except Exception:

            frappe.throw(
                _("Invalid file_urls format.")
            )

    if file_urls is None:

        file_urls = []

    # Single file support
    if file_url:

        file_urls.append(file_url)

    if not file_urls:

        frappe.throw(
            _("No file(s) provided.")
        )

    # PROCESS EACH CV

    for f_url in file_urls:

        try:

            # FILE URL

            current_file_url = f_url

            site_url = frappe.utils.get_url()

            if current_file_url.startswith(site_url):

                current_file_url = current_file_url.split(
                    site_url,
                    1
                )[1]

            if not current_file_url.startswith("/"):

                current_file_url = "/" + current_file_url

            # FILE PATH RESOLUTION

            file_path = None

            file_list = frappe.get_all(
                "File",
                filters={
                    "file_url": current_file_url
                },
                limit=1
            )

            if file_list:

                file_doc = frappe.get_doc(
                    "File",
                    file_list[0].name
                )

                file_path = file_doc.get_full_path()

            # Fallback path
            if (
                not file_path
                or not os.path.exists(file_path)
            ):

                path_parts = (
                    current_file_url
                    .lstrip("/")
                    .split("/")
                )

                file_path = os.path.abspath(
                    frappe.get_site_path(
                        *path_parts
                    )
                )

            # File not found
            if not os.path.exists(file_path):

                error_log.append(
                    f"File not found: {f_url}"
                )

                continue

            # GEMINI API

            api_key = frappe.conf.get(
                "gemini_api_key"
            )

            if not api_key:

                error_log.append(
                    f"{os.path.basename(f_url)}: "
                    "Gemini API key is missing."
                )

                continue

            # PROMPT

            prompt_path = frappe.get_app_path(
                "resume",
                "resume",
                "doctype",
                "pdf_upload",
                "parse_only_prompt.txt"
            )

            with open(
                prompt_path,
                "r",
                encoding="utf-8"
            ) as f:

                prompt_template = f.read()

            prompt_template = prompt_template.replace(
                "{{CURRENT_DATE}}",
                today_date
            )

            # JOB DESCRIPTION

            job_desc = frappe.db.get_value(
                "Job Opening",
                job_id,
                "description"
            )

            # FILE EXTENSION

            ext = os.path.splitext(
                file_path
            )[1].lower()

            # AI PARSING

            applicant_data = {}

            # STEP 1:
            # Extract text from ANY supported file

            text = extract_text_from_any_file(
                file_path
            )

            # STEP 2:
            # Parse extracted text

            if text:

                applicant_data = _safe_parse_text(
                    api_key,
                    prompt_template,
                    text,
                    job_id,
                    job_desc
                )

            # STEP 3:
            # Check whether email was found

            extracted_email = _normalize_email(
                applicant_data.get("email_id")
            )

            # STEP 4:
            # If email is missing, use direct file fallback
            #
            # This is now applied to ALL supported files.

            if not extracted_email:

                fallback_data = _safe_parse_pdf(
                    api_key,
                    prompt_template,
                    file_path,
                    job_id,
                    job_desc
                )

                # STEP 5:
                # Merge both parser results

                applicant_data = _merge_applicant_data(
                    applicant_data,
                    fallback_data
                )

            # ENSURE DICT

            if not isinstance(applicant_data, dict):

                applicant_data = {}

            # EMAIL

            email = _normalize_email(
                applicant_data.get("email_id")
            )

            # NAME

            name = (
                applicant_data.get(
                    "applicant_name"
                )
                or "Unknown"
            )

            # EMAIL NOT FOUND

            if not email:

                error_log.append(
                    f"Email not found in file: "
                    f"{os.path.basename(f_url)}"
                )

                continue

            # DUPLICATE CHECK

            if email in existing_email_set:

                duplicate_emails.append(
                    f"{name} ({email})"
                )

                continue

            # CREATE JOB APPLICANT

            applicant = frappe.get_doc(
                {
                    "doctype": "Job Applicant",

                    "applicant_name": name,

                    "email_id": email,

                    "phone_number": (
                        applicant_data.get(
                            "phone_number"
                        )
                        or ""
                    ),

                    "custom_phone_number_2": (
                        applicant_data.get(
                            "custom_phone_number_2"
                        )
                        or ""
                    ),

                    "resume_attachment": current_file_url,

                    "status": default_status,

                    "job_title": job_id,

                    "designation": designation,

                    "custom__current_company": (
                        applicant_data.get(
                            "custom__current_company"
                        )
                    ),

                    "custom__total_experience": (
                        applicant_data.get(
                            "custom__total_experience"
                        )
                    ),
                }
            )

            # INSERT

            applicant.insert(
                ignore_permissions=True
            )

            frappe.db.commit()

            # UPDATE EXISTING EMAIL SET

            existing_email_set.add(email)

            success_count += 1

        
        except Exception as e:

            frappe.log_error(
                title="CV Processing Error",
                message=frappe.get_traceback()
            )

            error_log.append(
                f"{os.path.basename(f_url)}: "
                f"{str(e)}"
            )

            # Continue processing remaining CVs
            continue


    message = ""

    if success_count:

        message += (
            f"{success_count} Applicant(s) "
            "Created Successfully\n\n"
        )

    if duplicate_emails:

        message += (
            "Duplicate Resumes Found "
            "(Skipped):\n"
        )

        message += (
            "\n".join(
                duplicate_emails
            )
            + "\n\n"
        )

    if error_log:

        message += "Errors:\n"

        message += "\n".join(
            error_log
        )

    if message:

        frappe.msgprint(
            message,
            title="CV Processing Result"
        )

    return {
        "status": "completed",
        "success_count": success_count,
    }