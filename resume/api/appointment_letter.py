# import frappe
# from frappe import _

# @frappe.whitelist(allow_guest=True)
# def get_accepted_job_offers():
#     """Get list of job offers with Accepted status"""
#     try:
#         offers = frappe.get_all(
#             "Job Offer",
#             filters={"status": "Accepted"},
#             fields=[
#                 "name",
#                 "applicant_name",
#                 "applicant_email", 
#                 "designation",
#                 "offer_date",
#                 "company",
#                 "status"
#             ],
#             order_by="modified desc"
#         )
        
#         return {
#             "success": True,
#             "data": offers
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), _("Error fetching accepted offers"))
#         return {
#             "success": False,
#             "message": str(e)
#         }

# @frappe.whitelist(allow_guest=True)
# def get_job_applicant_details(job_applicant):
#     """Get job applicant details"""
#     try:
#         applicant = frappe.get_doc("Job Applicant", job_applicant)
        
#         return {
#             "success": True,
#             "data": {
#                 "name": applicant.name,
#                 "applicant_name": applicant.applicant_name,
#                 "email_id": applicant.email_id,
#                 "phone_number": applicant.phone_number,
#                 "status": applicant.status
#             }
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), _("Error fetching applicant details"))
#         return {
#             "success": False,
#             "message": str(e)
#         }

# @frappe.whitelist(allow_guest=True)
# def get_appointment_letter_templates():
#     """Get all appointment letter templates"""
#     try:
#         templates = frappe.get_all(
#             "Appointment Letter Template",
#             fields=["name", "introduction"],
#             order_by="name"
#         )
        
#         return {
#             "success": True,
#             "data": templates
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), _("Error fetching templates"))
#         return {
#             "success": False,
#             "message": str(e)
#         }

# @frappe.whitelist(allow_guest=True)
# def get_appointment_letter_template_details(template_name):
#     """Get appointment letter template details with terms"""
#     try:
#         template = frappe.get_doc("Appointment Letter Template", template_name)
        
#         terms = []
#         if hasattr(template, 'terms'):
#             for term in template.terms:
#                 terms.append({
#                     "title": term.title if hasattr(term, 'title') else term.get('title', ''),
#                     "description": term.description if hasattr(term, 'description') else term.get('description', '')
#                 })
        
#         return {
#             "success": True,
#             "data": {
#                 "name": template.name,
#                 "introduction": template.introduction if hasattr(template, 'introduction') else '',
#                 "closing_notes": template.closing_notes if hasattr(template, 'closing_notes') else '',
#                 "terms": terms
#             }
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), _("Error fetching template details"))
#         return {
#             "success": False,
#             "message": str(e)
#         }

# @frappe.whitelist(allow_guest=True)
# def create_appointment_letter(data):
#     """Create a new appointment letter"""
#     try:
#         import json
#         if isinstance(data, str):
#             data = json.loads(data)
        
#         # Log the incoming data for debugging
#         frappe.logger().info(f"Creating appointment letter with data: {data}")
        
#         # Validate required fields
#         if not data.get("job_applicant"):
#             return {
#                 "success": False,
#                 "message": _("Job Applicant is required")
#             }
        
#         if not data.get("applicant_name"):
#             return {
#                 "success": False,
#                 "message": _("Applicant Name is required")
#             }
        
#         if not data.get("appointment_date"):
#             return {
#                 "success": False,
#                 "message": _("Appointment Date is required")
#             }
        
#         if not data.get("appointment_letter_template"):
#             return {
#                 "success": False,
#                 "message": _("Template is required")
#             }
        
#         # Check if appointment letter already exists for this job applicant
#         existing = frappe.db.exists(
#             "Appointment Letter",
#             {"job_applicant": data.get("job_applicant")}
#         )
        
#         if existing:
#             return {
#                 "success": False,
#                 "message": _("Appointment Letter already exists for this candidate")
#             }
        
#         # Create new Appointment Letter
#         appointment = frappe.get_doc({
#             "doctype": "Appointment Letter",
#             "job_applicant": data.get("job_applicant"),
#             "applicant_name": data.get("applicant_name"),
#             "company": data.get("company"),
#             "appointment_date": data.get("appointment_date"),
#             "appointment_letter_template": data.get("appointment_letter_template"),
#             "introduction": data.get("introduction", ""),
#             "closing_notes": data.get("closing_notes", "")
#         })
        
#         # Add terms
#         terms_list = []
#         for term in data.get("terms", []):
#             if term.get("title") or term.get("description"):
#                 appointment.append("terms", {
#                     "title": term.get("title", ""),
#                     "description": term.get("description", "")
#                 })
#                 terms_list.append({
#                     "title": term.get("title", ""),
#                     "description": term.get("description", "")
#                 })
        
#         # Insert with ignore_permissions for guest access
#         appointment.insert(ignore_permissions=True)
#         frappe.db.commit()
        
#         # Return complete data for preview
#         return {
#             "success": True,
#             "message": _("Appointment Letter created successfully"),
#             "data": {
#                 "name": appointment.name,
#                 "job_applicant": data.get("job_applicant"),
#                 "applicant_name": data.get("applicant_name"),
#                 "company": data.get("company"),
#                 "appointment_date": data.get("appointment_date"),
#                 "appointment_letter_template": data.get("appointment_letter_template"),
#                 "introduction": data.get("introduction", ""),
#                 "closing_notes": data.get("closing_notes", ""),
#                 "terms": terms_list
#             }
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), _("Error creating appointment letter"))
#         frappe.db.rollback()
#         return {
#             "success": False,
#             "message": str(e)
#         }

# @frappe.whitelist()
# def get_appointment_letter_list():
#     """Get list of all appointment letters"""
#     try:
#         letters = frappe.get_all(
#             "Appointment Letter",
#             fields=[
#                 "name",
#                 "job_applicant",
#                 "applicant_name",
#                 "company",
#                 "appointment_date",
#                 "status",
#                 "modified"
#             ],
#             order_by="modified desc"
#         )
        
#         return {
#             "success": True,
#             "data": letters
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), _("Error fetching appointment letters"))
#         return {
#             "success": False,
#             "message": str(e)
#         }

# @frappe.whitelist()
# def get_appointment_letter_details(appointment_letter_name):
#     """Get appointment letter details"""
#     try:
#         letter = frappe.get_doc("Appointment Letter", appointment_letter_name)
        
#         terms = []
#         if hasattr(letter, 'terms'):
#             for term in letter.terms:
#                 terms.append({
#                     "title": term.title if hasattr(term, 'title') else '',
#                     "description": term.description if hasattr(term, 'description') else ''
#                 })
        
#         return {
#             "success": True,
#             "data": {
#                 "name": letter.name,
#                 "job_applicant": letter.job_applicant if hasattr(letter, 'job_applicant') else '',
#                 "applicant_name": letter.applicant_name if hasattr(letter, 'applicant_name') else '',
#                 "company": letter.company if hasattr(letter, 'company') else '',
#                 "appointment_date": letter.appointment_date if hasattr(letter, 'appointment_date') else '',
#                 "appointment_letter_template": letter.appointment_letter_template if hasattr(letter, 'appointment_letter_template') else '',
#                 "introduction": letter.introduction if hasattr(letter, 'introduction') else '',
#                 "closing_notes": letter.closing_notes if hasattr(letter, 'closing_notes') else '',
#                 "terms": terms,
#                 "status": letter.status if hasattr(letter, 'status') else ''
#             }
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), _("Error fetching appointment letter details"))
#         return {
#             "success": False,
#             "message": str(e)
#         }


# @frappe.whitelist(allow_guest=True)
# def check_appointment_letter_exists(job_applicant):
#     """Check if appointment letter exists for a job applicant"""
#     try:
#         exists = frappe.db.exists(
#             "Appointment Letter",
#             {"job_applicant": job_applicant}
#         )
        
#         return {
#             "success": True,
#             "exists": bool(exists)
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), _("Error checking appointment letter"))
#         return {
#             "success": False,
#             "exists": False,
#             "message": str(e)
#         }

# @frappe.whitelist(allow_guest=True)
# def get_appointment_letter_by_job_applicant(job_applicant):
#     """Get appointment letter details by job applicant"""
#     try:
#         letter_name = frappe.db.get_value(
#             "Appointment Letter",
#             {"job_applicant": job_applicant},
#             "name"
#         )
        
#         if not letter_name:
#             return {
#                 "success": False,
#                 "message": _("Appointment Letter not found")
#             }
        
#         letter = frappe.get_doc("Appointment Letter", letter_name)
        
#         terms = []
#         if hasattr(letter, 'terms'):
#             for term in letter.terms:
#                 terms.append({
#                     "title": term.title if hasattr(term, 'title') else '',
#                     "description": term.description if hasattr(term, 'description') else ''
#                 })
        
#         return {
#             "success": True,
#             "data": {
#                 "name": letter.name,
#                 "job_applicant": letter.job_applicant if hasattr(letter, 'job_applicant') else '',
#                 "applicant_name": letter.applicant_name if hasattr(letter, 'applicant_name') else '',
#                 "company": letter.company if hasattr(letter, 'company') else '',
#                 "appointment_date": letter.appointment_date if hasattr(letter, 'appointment_date') else '',
#                 "appointment_letter_template": letter.appointment_letter_template if hasattr(letter, 'appointment_letter_template') else '',
#                 "introduction": letter.introduction if hasattr(letter, 'introduction') else '',
#                 "closing_notes": letter.closing_notes if hasattr(letter, 'closing_notes') else '',
#                 "terms": terms,
#                 "status": letter.status if hasattr(letter, 'status') else ''
#             }
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), _("Error fetching appointment letter by job applicant"))
#         return {
#             "success": False,
#             "message": str(e)
#         }


import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_accepted_job_offers():
    """Get list of job offers with Accepted status"""
    try:
        offers = frappe.get_all(
            "Job Offer",
            filters={"status": "Accepted"},
            fields=[
                "name",
                "job_applicant",  # Added this field - the actual Job Applicant ID
                "applicant_name",
                "applicant_email", 
                "designation",
                "offer_date",
                "company",
                "status"
            ],
            order_by="modified desc"
        )
        
        return {
            "success": True,
            "data": offers
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching accepted offers"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True)
def get_job_applicant_details(job_applicant):
    """Get job applicant details"""
    try:
        applicant = frappe.get_doc("Job Applicant", job_applicant)
        
        return {
            "success": True,
            "data": {
                "name": applicant.name,
                "applicant_name": applicant.applicant_name,
                "email_id": applicant.email_id,
                "phone_number": applicant.phone_number,
                "status": applicant.status
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching applicant details"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True)
def get_appointment_letter_templates():
    """Get all appointment letter templates"""
    try:
        templates = frappe.get_all(
            "Appointment Letter Template",
            fields=["name", "introduction"],
            order_by="name"
        )
        
        return {
            "success": True,
            "data": templates
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching templates"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True)
def get_appointment_letter_template_details(template_name):
    """Get appointment letter template details with terms"""
    try:
        template = frappe.get_doc("Appointment Letter Template", template_name)
        
        terms = []
        if hasattr(template, 'terms'):
            for term in template.terms:
                terms.append({
                    "title": term.title if hasattr(term, 'title') else term.get('title', ''),
                    "description": term.description if hasattr(term, 'description') else term.get('description', '')
                })
        
        return {
            "success": True,
            "data": {
                "name": template.name,
                "introduction": template.introduction if hasattr(template, 'introduction') else '',
                "closing_notes": template.closing_notes if hasattr(template, 'closing_notes') else '',
                "terms": terms
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching template details"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True)
def create_appointment_letter(data):
    """Create a new appointment letter"""
    try:
        import json
        if isinstance(data, str):
            data = json.loads(data)
        
        # Log the incoming data for debugging
        frappe.logger().info(f"Creating appointment letter with data: {data}")
        
        # Validate required fields
        if not data.get("job_applicant"):
            return {
                "success": False,
                "message": _("Job Applicant is required")
            }
        
        if not data.get("applicant_name"):
            return {
                "success": False,
                "message": _("Applicant Name is required")
            }
        
        if not data.get("appointment_date"):
            return {
                "success": False,
                "message": _("Appointment Date is required")
            }
        
        if not data.get("appointment_letter_template"):
            return {
                "success": False,
                "message": _("Template is required")
            }
        
        # Check if appointment letter already exists for this job applicant
        existing = frappe.db.exists(
            "Appointment Letter",
            {"job_applicant": data.get("job_applicant")}
        )
        
        if existing:
            return {
                "success": False,
                "message": _("Appointment Letter already exists for this candidate")
            }
        
        # Create new Appointment Letter
        appointment = frappe.get_doc({
            "doctype": "Appointment Letter",
            "job_applicant": data.get("job_applicant"),
            "applicant_name": data.get("applicant_name"),
            "company": data.get("company"),
            "appointment_date": data.get("appointment_date"),
            "appointment_letter_template": data.get("appointment_letter_template"),
            "introduction": data.get("introduction", ""),
            "closing_notes": data.get("closing_notes", "")
        })
        
        # Add terms
        terms_list = []
        for term in data.get("terms", []):
            if term.get("title") or term.get("description"):
                appointment.append("terms", {
                    "title": term.get("title", ""),
                    "description": term.get("description", "")
                })
                terms_list.append({
                    "title": term.get("title", ""),
                    "description": term.get("description", "")
                })
        
        # Insert with ignore_permissions for guest access
        appointment.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Return complete data for preview
        return {
            "success": True,
            "message": _("Appointment Letter created successfully"),
            "data": {
                "name": appointment.name,
                "job_applicant": data.get("job_applicant"),
                "applicant_name": data.get("applicant_name"),
                "company": data.get("company"),
                "appointment_date": data.get("appointment_date"),
                "appointment_letter_template": data.get("appointment_letter_template"),
                "introduction": data.get("introduction", ""),
                "closing_notes": data.get("closing_notes", ""),
                "terms": terms_list
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error creating appointment letter"))
        frappe.db.rollback()
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def get_appointment_letter_list():
    """Get list of all appointment letters"""
    try:
        letters = frappe.get_all(
            "Appointment Letter",
            fields=[
                "name",
                "job_applicant",
                "applicant_name",
                "company",
                "appointment_date",
                "status",
                "modified"
            ],
            order_by="modified desc"
        )
        
        return {
            "success": True,
            "data": letters
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching appointment letters"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def get_appointment_letter_details(appointment_letter_name):
    """Get appointment letter details"""
    try:
        letter = frappe.get_doc("Appointment Letter", appointment_letter_name)
        
        terms = []
        if hasattr(letter, 'terms'):
            for term in letter.terms:
                terms.append({
                    "title": term.title if hasattr(term, 'title') else '',
                    "description": term.description if hasattr(term, 'description') else ''
                })
        
        return {
            "success": True,
            "data": {
                "name": letter.name,
                "job_applicant": letter.job_applicant if hasattr(letter, 'job_applicant') else '',
                "applicant_name": letter.applicant_name if hasattr(letter, 'applicant_name') else '',
                "company": letter.company if hasattr(letter, 'company') else '',
                "appointment_date": letter.appointment_date if hasattr(letter, 'appointment_date') else '',
                "appointment_letter_template": letter.appointment_letter_template if hasattr(letter, 'appointment_letter_template') else '',
                "introduction": letter.introduction if hasattr(letter, 'introduction') else '',
                "closing_notes": letter.closing_notes if hasattr(letter, 'closing_notes') else '',
                "terms": terms,
                "status": letter.status if hasattr(letter, 'status') else ''
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching appointment letter details"))
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def check_appointment_letter_exists(job_applicant):
    """Check if appointment letter exists for a job applicant"""
    try:
        exists = frappe.db.exists(
            "Appointment Letter",
            {"job_applicant": job_applicant}
        )
        
        return {
            "success": True,
            "exists": bool(exists)
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error checking appointment letter"))
        return {
            "success": False,
            "exists": False,
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True)
def get_appointment_letter_by_job_applicant(job_applicant):
    """Get appointment letter details by job applicant"""
    try:
        letter_name = frappe.db.get_value(
            "Appointment Letter",
            {"job_applicant": job_applicant},
            "name"
        )
        
        if not letter_name:
            return {
                "success": False,
                "message": _("Appointment Letter not found")
            }
        
        letter = frappe.get_doc("Appointment Letter", letter_name)
        
        terms = []
        if hasattr(letter, 'terms'):
            for term in letter.terms:
                terms.append({
                    "title": term.title if hasattr(term, 'title') else '',
                    "description": term.description if hasattr(term, 'description') else ''
                })
        
        return {
            "success": True,
            "data": {
                "name": letter.name,
                "job_applicant": letter.job_applicant if hasattr(letter, 'job_applicant') else '',
                "applicant_name": letter.applicant_name if hasattr(letter, 'applicant_name') else '',
                "company": letter.company if hasattr(letter, 'company') else '',
                "appointment_date": letter.appointment_date if hasattr(letter, 'appointment_date') else '',
                "appointment_letter_template": letter.appointment_letter_template if hasattr(letter, 'appointment_letter_template') else '',
                "introduction": letter.introduction if hasattr(letter, 'introduction') else '',
                "closing_notes": letter.closing_notes if hasattr(letter, 'closing_notes') else '',
                "terms": terms,
                "status": letter.status if hasattr(letter, 'status') else ''
            }
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching appointment letter by job applicant"))
        return {
            "success": False,
            "message": str(e)
        }
        