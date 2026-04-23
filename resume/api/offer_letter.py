import frappe
from datetime import datetime
import json

@frappe.whitelist(allow_guest=True)
def create_job_offer():
    """Create a new job offer"""
    data = frappe.form_dict
    frappe.log("Received job offer data: {data}".format(data=json.dumps(dict(data), indent=2)))

    # Define required fields
    required_fields = ["job_applicant", "applicant_name", "designation", "company", "status",]
    for field in required_fields:
        if not data.get(field):
            frappe.throw(f"{field} is required")

    # Validate status
    status = data.get("status")
    frappe.log(f"status received: {status}")
    valid_statuses = ["Awaiting Response", "Accepted", "Rejected", "Pending"]
    if not status or status not in valid_statuses:
        frappe.throw(f"Invalid or missing status. Must be one of {', '.join(valid_statuses)}")

    try:
        # Create the Job Offer document
        job_offer_doc = frappe.get_doc({
            "doctype": "Job Offer",
            "job_applicant": data.job_applicant,
            "applicant_name": data.applicant_name,
            "applicant_email": data.get("applicant_email"),
            "offer_date": data.get("offer_date"),
            "designation": data.designation,
            "company": data.company,
            "status": status,
            "job_offer_term_template": data.get("job_offer_template"),
        })
        
        # Add job offer terms if provided
        if data.get("offer_terms"):
            offer_terms = json.loads(data.offer_terms) if isinstance(data.offer_terms, str) else data.offer_terms
            for term in offer_terms:
                if term.get("offer_term") and term.get("value_description"):
                    job_offer_doc.append("offer_terms", {
                        "offer_term": term.get("offer_term"),
                        "value": term.get("value_description")
                    })
        
        job_offer_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.log(f"Created job offer: {job_offer_doc.name}, status: {job_offer_doc.status}")
        return {
            "message": f"Job Offer {job_offer_doc.name} created successfully.",
            "doc": job_offer_doc.as_dict()
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Job Offer Creation Failed")
        frappe.throw(f"Failed to create job offer: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_job_offer_list():
    """Get list of all job offers"""
    try:
        job_offers = frappe.get_all(
            "Job Offer",
            fields=[
                "name",
                "job_applicant",
                "applicant_name",
                "applicant_email",
                "offer_date",
                "designation",
                "company",
                "status",
                "job_offer_term_template",
                "creation",
                "modified"
            ],
            order_by="offer_date desc"
        )
        
        # Get offer terms for each job offer
        for offer in job_offers:
            offer_terms = frappe.get_all(
                "Job Offer Term",
                filters={"parent": offer.name},
                fields=["offer_term", "value"]
            )
            offer["offer_terms"] = offer_terms
        
        return {
            "message": "Job offers fetched successfully",
            "data": job_offers
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Job Offer List Fetch Failed")
        frappe.throw("Failed to fetch job offers")


@frappe.whitelist(allow_guest=True)
def get_job_offer_details(job_offer_name):
    """Get details of a specific job offer"""
    try:
        if not job_offer_name:
            frappe.throw("Job offer name is required")
        
        job_offer = frappe.get_doc("Job Offer", job_offer_name)
        
        # Get offer terms
        offer_terms = frappe.get_all(
            "Job Offer Term",
            filters={"parent": job_offer_name},
            fields=["offer_term", "value", "name"]
        )
        
        job_offer_dict = job_offer.as_dict()
        job_offer_dict["offer_terms"] = offer_terms
        
        return {
            "message": "Job offer details fetched successfully",
            "data": job_offer_dict
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Job Offer Details Fetch Failed")
        frappe.throw(f"Failed to fetch job offer details: {str(e)}")


@frappe.whitelist(allow_guest=True)
def update_job_offer():
    """Update an existing job offer"""
    data = frappe.form_dict
    frappe.log("Updating job offer: {data}".format(data=json.dumps(dict(data), indent=2)))

    job_offer_name = data.get("name")
    if not job_offer_name:
        frappe.throw("Job offer name is required for update")

    try:
        job_offer_doc = frappe.get_doc("Job Offer", job_offer_name)
        
        # Update fields if provided
        if data.get("job_applicant"):
            job_offer_doc.job_applicant = data.job_applicant
        if data.get("applicant_name"):
            job_offer_doc.applicant_name = data.applicant_name
        if data.get("applicant_email"):
            job_offer_doc.applicant_email = data.applicant_email
        if data.get("offer_date"):
            job_offer_doc.offer_date = data.offer_date
        if data.get("designation"):
            job_offer_doc.designation = data.designation
        if data.get("company"):
            job_offer_doc.company = data.company
        if data.get("status"):
            job_offer_doc.status = data.status
        if data.get("job_offer_template"):
            job_offer_doc.job_offer_term_template = data.job_offer_template
        
        # Update offer terms if provided
        if data.get("offer_terms"):
            # Clear existing offer terms
            job_offer_doc.offer_terms = []
            
            offer_terms = json.loads(data.offer_terms) if isinstance(data.offer_terms, str) else data.offer_terms
            for term in offer_terms:
                if term.get("offer_term") and term.get("value_description"):
                    job_offer_doc.append("offer_terms", {
                        "offer_term": term.get("offer_term"),
                        "value": term.get("value_description")
                    })
        
        job_offer_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.log(f"Updated job offer: {job_offer_doc.name}")
        return {
            "message": f"Job Offer {job_offer_doc.name} updated successfully.",
            "doc": job_offer_doc.as_dict()
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Job Offer Update Failed")
        frappe.throw(f"Failed to update job offer: {str(e)}")


@frappe.whitelist(allow_guest=True)
def delete_job_offer(job_offer_name):
    """Delete a job offer"""
    try:
        if not job_offer_name:
            frappe.throw("Job offer name is required")
        
        frappe.delete_doc("Job Offer", job_offer_name, ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "message": f"Job Offer {job_offer_name} deleted successfully"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Job Offer Deletion Failed")
        frappe.throw(f"Failed to delete job offer: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_job_applicants():
    """Get list of job applicants for dropdown"""
    try:
        applicants = frappe.get_all(
            "Job Applicant",
            fields=["name", "applicant_name", "email_id"],
            order_by="creation desc"
        )
        
        return {
            "message": "Job applicants fetched successfully",
            "data": applicants
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Job Applicants Fetch Failed")
        frappe.throw("Failed to fetch job applicants")


@frappe.whitelist(allow_guest=True)
def get_job_offer_templates():
    """Get list of job offer term templates"""
    try:
        # Try to get templates with error handling for different field names
        templates = frappe.get_all(
            "Job Offer Term Template",
            fields=["name"],
            order_by="name"
        )
        
        # Get the actual field names from meta
        if templates:
            # Try to get the template name field dynamically
            result = []
            for template in templates:
                try:
                    doc = frappe.get_doc("Job Offer Term Template", template.name)
                    result.append({
                        "name": doc.name,
                        "offer_term_template_name": doc.get("offer_term_template_name") or doc.name
                    })
                except:
                    result.append({
                        "name": template.name,
                        "offer_term_template_name": template.name
                    })
            
            return {
                "message": "Job offer templates fetched successfully",
                "data": result
            }
        
        return {
            "message": "Job offer templates fetched successfully",
            "data": []
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Job Offer Templates Fetch Failed")
        # Return empty list instead of throwing error
        return {
            "message": "No templates found",
            "data": []
        }


@frappe.whitelist(allow_guest=True)
def get_companies():
    """Get list of companies"""
    try:
        companies = frappe.get_all(
            "Company",
            fields=["name", "company_name"],
            order_by="name"
        )
        
        return {
            "message": "Companies fetched successfully",
            "data": companies
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Companies Fetch Failed")
        frappe.throw("Failed to fetch companies")


@frappe.whitelist(allow_guest=True)
def get_designations():
    """Get list of designations"""
    try:
        designations = frappe.get_all(
            "Designation",
            fields=["name", "designation_name"],
            order_by="name"
        )
        
        return {
            "message": "Designations fetched successfully",
            "data": designations
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Designations Fetch Failed")
        frappe.throw("Failed to fetch designations")

@frappe.whitelist(allow_guest=True)
def get_template_terms(template_name):
    """Get offer terms from a template"""
    try:
        if not template_name:
            frappe.throw("Template name is required")

        template = frappe.get_doc("Job Offer Term Template", template_name)

        terms = []
        if hasattr(template, 'offer_terms'):
            for term in template.offer_terms:
                terms.append({
                    "offer_term": getattr(term, "offer_term", "") or getattr(term, "term", "") or getattr(term, "title", ""),
                    "value": getattr(term, "value", "") or getattr(term, "desc", "") or getattr(term, "description", "")
                })

        return {
            "message": "Template terms fetched successfully",
            "data": terms
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Template Terms Fetch Failed")
        return {
            "message": "No terms found",
            "data": []
        }
