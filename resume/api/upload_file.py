# import frappe
# from frappe import _
# from frappe.utils import now_datetime
# import json

# @frappe.whitelist()
# def get_applicant_document(name):
#     """Get Applicant Document details with linked data"""
#     try:
#         if not frappe.db.exists("Applicant Document", name):
#             return {    
#                 "status": "error",
#                 "message": f"Applicant Document {name} not found"
#             }
        
#         doc = frappe.get_doc("Applicant Document", name)
        
#         applicant_data = {}
#         if doc.applicant_name:
#             applicant_data = frappe.db.get_value(
#                 "Job Applicant",
#                 doc.applicant_name,
#                 ["applicant_name", "email_id", "phone_number"],
#                 as_dict=True
#             ) or {}
        
#         employee_data = {}
#         if doc.employee:
#             employee_data = frappe.db.get_value(
#                 "Employee",
#                 doc.employee,
#                 ["employee_name", "personal_email", "cell_number"],
#                 as_dict=True
#             ) or {}
        
#         return {
#             "status": "success",
#             "data": {
#                 **doc.as_dict(),
#                 "applicant_details": applicant_data,
#                 "employee_details": employee_data
#             }
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Get Applicant Document Error")
#         return {
#             "status": "error",
#             "message": str(e)
#         }


# @frappe.whitelist()
# def get_applicant_documents_list(filters=None, limit_start=0, limit_page_length=20):
#     """Get list of Applicant Documents with pagination"""
#     try:
#         filters_dict = json.loads(filters) if filters else {}
        
#         documents = frappe.get_all(
#             "Applicant Document",
#             filters=filters_dict,
#             fields=[
#                 "name", "applicant_name", "employee", "creation", "modified",
#                 "aadhar_card", "passport", "experience", "education",
#                 "bank_details", "pan", "medical", "photos"
#             ],
#             start=int(limit_start),
#             page_length=int(limit_page_length),
#             order_by="creation desc"
#         )
        
#         for doc in documents:
#             if doc.applicant_name:
#                 applicant = frappe.db.get_value(
#                     "Job Applicant",
#                     doc.applicant_name,
#                     ["applicant_name", "email_id"],
#                     as_dict=True
#                 )
#                 doc["applicant_details"] = applicant or {}
            
#             if doc.employee:
#                 employee = frappe.db.get_value(
#                     "Employee",
#                     doc.employee,
#                     ["employee_name", "personal_email"],
#                     as_dict=True
#                 )
#                 doc["employee_details"] = employee or {}
        
#         return {
#             "status": "success",
#             "data": documents,
#             "total": frappe.db.count("Applicant Document", filters_dict)
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Get Applicant Documents List Error")
#         return {
#             "status": "error",
#             "message": str(e)
#         }


# @frappe.whitelist()
# def delete_applicant_document(name):
#     """Delete Applicant Document and associated files"""
#     try:
#         if not frappe.db.exists("Applicant Document", name):
#             return {
#                 "status": "error",
#                 "message": f"Applicant Document {name} not found"
#             }
        
#         doc = frappe.get_doc("Applicant Document", name)
        
#         file_fields = [
#             "aadhar_card", "passport", "experience", "education",
#             "bank_details", "pan", "medical", "photos"
#         ]
        
#         # Delete associated files
#         for field in file_fields:
#             file_url = doc.get(field)
#             if file_url:
#                 try:
#                     file_doc = frappe.get_doc("File", {"file_url": file_url})
#                     file_doc.delete(ignore_permissions=True)
#                 except:
#                     pass
        
#         # Delete the document
#         frappe.delete_doc("Applicant Document", name, ignore_permissions=True)
#         frappe.db.commit()
        
#         return {
#             "status": "success",
#             "message": "Applicant Document deleted successfully"
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Delete Applicant Document Error")
#         return {
#             "status": "error",
#             "message": str(e)
#         }


# @frappe.whitelist()
# def update_applicant_document(name, data):
#     """Update existing Applicant Document with partial updates support"""
#     try:
#         if not frappe.db.exists("Applicant Document", name):
#             return {
#                 "status": "error",
#                 "message": f"Applicant Document {name} not found"
#             }
        
#         doc = frappe.get_doc("Applicant Document", name)
        
#         # Parse data if it's a string
#         if isinstance(data, str):
#             data = json.loads(data)
        
#         # Update applicant_name if provided
#         if data.get("applicant_name"):
#             if not frappe.db.exists("Job Applicant", data["applicant_name"]):
#                 return {
#                     "status": "error",
#                     "message": f"Job Applicant {data['applicant_name']} does not exist"
#                 }
#             doc.applicant_name = data["applicant_name"]
        
#         # Update employee if provided
#         if data.get("employee"):
#             if not frappe.db.exists("Employee", data["employee"]):
#                 return {
#                     "status": "error",
#                     "message": f"Employee {data['employee']} does not exist"
#                 }
#             doc.employee = data["employee"]
        
#         # Update file fields only if new values are provided
#         file_fields = [
#             "aadhar_card", "passport", "experience", "education",
#             "bank_details", "pan", "medical", "photos"
#         ]
        
#         for field in file_fields:
#             if field in data and data[field]:
#                 # Only update if a new file URL is provided
#                 doc.set(field, data[field])
        
#         doc.save(ignore_permissions=True)
#         frappe.db.commit()
        
#         return {
#             "status": "success",
#             "message": "Applicant Document updated successfully",
#             "data": doc.as_dict()
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Update Applicant Document Error")
#         return {
#             "status": "error",
#             "message": str(e)
#         }


# @frappe.whitelist()
# def get_applicant_document_by_applicant(applicant_name):
#     """Get Applicant Document by applicant name"""
#     try:
#         if not frappe.db.exists("Job Applicant", applicant_name):
#             return {
#                 "status": "error",
#                 "message": f"Job Applicant {applicant_name} not found"
#             }
        
#         # Check if document exists for this applicant
#         doc_name = frappe.db.get_value(
#             "Applicant Document",
#             {"applicant_name": applicant_name},
#             "name"
#         )
        
#         if not doc_name:
#             return {
#                 "status": "success",
#                 "message": "No document found for this applicant",
#                 "data": None
#             }
        
#         # Get the full document
#         doc = frappe.get_doc("Applicant Document", doc_name)
        
#         applicant_data = {}
#         if doc.applicant_name:
#             applicant_data = frappe.db.get_value(
#                 "Job Applicant",
#                 doc.applicant_name,
#                 ["applicant_name", "email_id", "phone_number"],
#                 as_dict=True
#             ) or {}
        
#         employee_data = {}
#         if doc.employee:
#             employee_data = frappe.db.get_value(
#                 "Employee",
#                 doc.employee,
#                 ["employee_name", "personal_email", "cell_number"],
#                 as_dict=True
#             ) or {}
        
#         return {
#             "status": "success",
#             "data": {
#                 **doc.as_dict(),
#                 "applicant_details": applicant_data,
#                 "employee_details": employee_data
#             }
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Get Applicant Document By Applicant Error")
#         return {
#             "status": "error",
#             "message": str(e)
#         }


# @frappe.whitelist()
# def get_document_upload_status(applicant_name):
#     """Get upload status for all documents for a specific applicant"""
#     try:
#         if not frappe.db.exists("Job Applicant", applicant_name):
#             return {
#                 "status": "error",
#                 "message": f"Job Applicant {applicant_name} not found"
#             }
        
#         doc_name = frappe.db.get_value(
#             "Applicant Document",
#             {"applicant_name": applicant_name},
#             "name"
#         )
        
#         if not doc_name:
#             return {
#                 "status": "success",
#                 "message": "No documents uploaded yet",
#                 "uploaded": {},
#                 "missing": [
#                     "aadhar_card", "passport", "experience", "education",
#                     "bank_details", "pan", "medical", "photos"
#                 ],
#                 "upload_count": 0,
#                 "total_count": 8
#             }
        
#         doc = frappe.get_doc("Applicant Document", doc_name)
        
#         file_fields = [
#             "aadhar_card", "passport", "experience", "education",
#             "bank_details", "pan", "medical", "photos"
#         ]
        
#         uploaded = {}
#         missing = []
        
#         for field in file_fields:
#             value = doc.get(field)
#             if value:
#                 uploaded[field] = value
#             else:
#                 missing.append(field)
        
#         return {
#             "status": "success",
#             "document_id": doc_name,
#             "uploaded": uploaded,
#             "missing": missing,
#             "upload_count": len(uploaded),
#             "total_count": len(file_fields)
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Get Document Upload Status Error")
#         return {
#             "status": "error",
#             "message": str(e)
#         }









    

import frappe
from frappe import _
from frappe.utils import now_datetime
import json

@frappe.whitelist()
def get_applicant_document(name):
    """Get Applicant Document details with linked data"""
    try:
        if not frappe.db.exists("Applicant Document", name):
            return {
                "status": "error",
                "message": f"Applicant Document {name} not found"
            }
        
        doc = frappe.get_doc("Applicant Document", name)
        
        applicant_data = {}
        if doc.applicant_name:
            applicant_data = frappe.db.get_value(
                "Job Applicant",
                doc.applicant_name,
                ["applicant_name", "email_id", "phone_number"],
                as_dict=True
            ) or {}
        
        employee_data = {}
        if doc.employee:
            employee_data = frappe.db.get_value(
                "Employee",
                doc.employee,
                ["employee_name", "personal_email", "cell_number"],
                as_dict=True
            ) or {}
        
        return {
            "status": "success",
            "data": {
                **doc.as_dict(),
                "applicant_details": applicant_data,
                "employee_details": employee_data
            }
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Applicant Document Error")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def get_applicant_documents_list(filters=None, limit_start=0, limit_page_length=20):
    """Get list of Applicant Documents with pagination"""
    try:
        filters_dict = json.loads(filters) if filters else {}
        
        documents = frappe.get_all(
            "Applicant Document",
            filters=filters_dict,
            fields=[
                "name", "applicant_name", "employee", "creation", "modified",
                "aadhar_card", "passport", "experience", "education",
                "bank_details", "pan", "medical", "photos",
                "custom_background_verification", "custom_salary_slip", 
                "custom_additional_document"
            ],
            start=int(limit_start),
            page_length=int(limit_page_length),
            order_by="creation desc"
        )
        
        for doc in documents:
            if doc.applicant_name:
                applicant = frappe.db.get_value(
                    "Job Applicant",
                    doc.applicant_name,
                    ["applicant_name", "email_id"],
                    as_dict=True
                )
                doc["applicant_details"] = applicant or {}
            
            if doc.employee:
                employee = frappe.db.get_value(
                    "Employee",
                    doc.employee,
                    ["employee_name", "personal_email"],
                    as_dict=True
                )
                doc["employee_details"] = employee or {}
        
        return {
            "status": "success",
            "data": documents,
            "total": frappe.db.count("Applicant Document", filters_dict)
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Applicant Documents List Error")
        return {
            "status": "error",
            "message": str(e)
        }


def delete_file_safely(file_url):
    """Helper function to safely delete a file"""
    if not file_url:
        return
    
    try:
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        file_doc.delete(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Error deleting file {file_url}: {str(e)}", "File Deletion Error")


def delete_multiple_files(field_value):
    """Helper function to delete multiple files stored as JSON array"""
    if not field_value:
        return
    
    try:
        file_urls = json.loads(field_value)
        if isinstance(file_urls, list):
            for url in file_urls:
                delete_file_safely(url)
        else:
            delete_file_safely(field_value)
    except json.JSONDecodeError:
        delete_file_safely(field_value)


@frappe.whitelist()
def delete_applicant_document(name):
    """Delete Applicant Document and associated files"""
    try:
        if not frappe.db.exists("Applicant Document", name):
            return {
                "status": "error",
                "message": f"Applicant Document {name} not found"
            }
        
        doc = frappe.get_doc("Applicant Document", name)
        
        single_file_fields = [
            "aadhar_card", "passport", "experience", "education",
            "bank_details", "pan", "medical", "photos"
        ]
        
        for field in single_file_fields:
            file_url = doc.get(field)
            delete_file_safely(file_url)
        
        multiple_file_fields = [
            "custom_background_verification",
            "custom_salary_slip",
            "custom_additional_document"
        ]
        
        for field in multiple_file_fields:
            field_value = doc.get(field)
            delete_multiple_files(field_value)
        
        frappe.delete_doc("Applicant Document", name, ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "Applicant Document deleted successfully"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Delete Applicant Document Error")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def update_applicant_document(name, data):
    """Update existing Applicant Document with partial updates support"""
    try:
        if not frappe.db.exists("Applicant Document", name):
            return {
                "status": "error",
                "message": f"Applicant Document {name} not found"
            }
        
        doc = frappe.get_doc("Applicant Document", name)
        
        if isinstance(data, str):
            data = json.loads(data)
        
        if data.get("applicant_name"):
            if not frappe.db.exists("Job Applicant", data["applicant_name"]):
                return {
                    "status": "error",
                    "message": f"Job Applicant {data['applicant_name']} does not exist"
                }
            doc.applicant_name = data["applicant_name"]
        
        if data.get("employee"):
            if not frappe.db.exists("Employee", data["employee"]):
                return {
                    "status": "error",
                    "message": f"Employee {data['employee']} does not exist"
                }
            doc.employee = data["employee"]
        
        single_file_fields = [
            "aadhar_card", "passport", "experience", "education",
            "bank_details", "pan", "medical", "photos"
        ]
        
        for field in single_file_fields:
            if field in data and data[field]:
                doc.set(field, data[field])
        
        multiple_file_fields = [
            "custom_background_verification",
            "custom_salary_slip",
            "custom_additional_document"
        ]
        
        for field in multiple_file_fields:
            if field in data and data[field]:
                doc.set(field, data[field])
        
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "Applicant Document updated successfully",
            "data": doc.as_dict()
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Applicant Document Error")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def get_applicant_document_by_applicant(applicant_name):
    """Get Applicant Document by applicant name"""
    try:
        if not frappe.db.exists("Job Applicant", applicant_name):
            return {
                "status": "error",
                "message": f"Job Applicant {applicant_name} not found"
            }
        
        doc_name = frappe.db.get_value(
            "Applicant Document",
            {"applicant_name": applicant_name},
            "name"
        )
        
        if not doc_name:
            return {
                "status": "success",
                "message": "No document found for this applicant",
                "data": None
            }
        
        doc = frappe.get_doc("Applicant Document", doc_name)
        
        applicant_data = {}
        if doc.applicant_name:
            applicant_data = frappe.db.get_value(
                "Job Applicant",
                doc.applicant_name,
                ["applicant_name", "email_id", "phone_number"],
                as_dict=True
            ) or {}
        
        employee_data = {}
        if doc.employee:
            employee_data = frappe.db.get_value(
                "Employee",
                doc.employee,
                ["employee_name", "personal_email", "cell_number"],
                as_dict=True
            ) or {}
        
        return {
            "status": "success",
            "data": {
                **doc.as_dict(),
                "applicant_details": applicant_data,
                "employee_details": employee_data
            }
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Applicant Document By Applicant Error")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def get_document_upload_status(applicant_name):
    """Get upload status for all documents for a specific applicant"""
    try:
        if not frappe.db.exists("Job Applicant", applicant_name):
            return {
                "status": "error",
                "message": f"Job Applicant {applicant_name} not found"
            }
        
        doc_name = frappe.db.get_value(
            "Applicant Document",
            {"applicant_name": applicant_name},
            "name"
        )
        
        if not doc_name:
            return {
                "status": "success",
                "message": "No documents uploaded yet",
                "uploaded": {},
                "missing": [
                    "aadhar_card", "passport", "experience", "education",
                    "bank_details", "pan", "medical", "photos",
                    "custom_background_verification", "custom_salary_slip",
                    "custom_additional_document"
                ],
                "upload_count": 0,
                "total_count": 11
            }
        
        doc = frappe.get_doc("Applicant Document", doc_name)
        
        file_fields = [
            "aadhar_card", "passport", "experience", "education",
            "bank_details", "pan", "medical", "photos",
            "custom_background_verification", "custom_salary_slip",
            "custom_additional_document"
        ]
        
        uploaded = {}
        missing = []
        
        for field in file_fields:
            value = doc.get(field)
            if value:
                if field in ["custom_background_verification", "custom_salary_slip", "custom_additional_document"]:
                    try:
                        files = json.loads(value)
                        if isinstance(files, list) and len(files) > 0:
                            uploaded[field] = files
                        else:
                            missing.append(field)
                    except:
                        uploaded[field] = value
                else:
                    uploaded[field] = value
            else:
                missing.append(field)
        
        return {
            "status": "success",
            "document_id": doc_name,
            "uploaded": uploaded,
            "missing": missing,
            "upload_count": len(uploaded),
            "total_count": len(file_fields)
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Document Upload Status Error")
        return {
            "status": "error",
            "message": str(e)
        }

        