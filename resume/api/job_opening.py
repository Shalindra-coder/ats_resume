import frappe
from datetime import datetime, timezone
import json

@frappe.whitelist(allow_guest=True)
def create_job_opening():
    frappe.logger().info("=== CREATE JOB OPENING STARTED ===")
    
    try:
        # Step 1: Get data
        frappe.logger().info("Step 1: Getting form data")
        data = frappe.form_dict
        frappe.logger().info(f"Received data: {json.dumps(dict(data), indent=2)}")

        # Step 2: Validate required fields
        frappe.logger().info("Step 2: Validating required fields")
        if not data.get("job_title"):
            frappe.logger().error("Validation failed: job_title missing")
            return {"success": False, "message": "Job title is required"}
        if not data.get("designation"):
            frappe.logger().error("Validation failed: designation missing")
            return {"success": False, "message": "Designation is required"}
        if not data.get("company"):
            frappe.logger().error("Validation failed: company missing")
            return {"success": False, "message": "Company is required"}

        # Step 3: Validate status
        frappe.logger().info("Step 3: Validating status")
        status = data.get("status", "Open")
        valid_statuses = ["Open", "Closed", "On Hold"]
        if status not in valid_statuses:
            return {"success": False, "message": f"Invalid status. Must be one of {', '.join(valid_statuses)}"}

        # Step 4: Process salary ranges
        frappe.logger().info("Step 4: Processing salary ranges")
        lower_range_final = None
        upper_range_final = None
        
        lower_range_val = data.get("lower_range")
        upper_range_val = data.get("upper_range")
        
        frappe.logger().info(f"Lower range: {lower_range_val}, Upper range: {upper_range_val}")

        if lower_range_val and upper_range_val:
            try:
                lower = float(lower_range_val)
                upper = float(upper_range_val)
                
                if lower <= 0 or upper <= 0:
                    return {"success": False, "message": "Salary ranges must be positive numbers"}
                if lower >= upper:
                    return {"success": False, "message": "Minimum salary must be less than maximum salary"}
                
                lower_range_final = lower
                upper_range_final = upper
                frappe.logger().info(f"Salary range processed: {lower_range_final} - {upper_range_final}")
            except (ValueError, TypeError) as e:
                frappe.logger().error(f"Salary conversion error: {str(e)}")
                return {"success": False, "message": "Salary ranges must be valid numbers"}

        # Step 5: Convert boolean values
        frappe.logger().info("Step 5: Converting boolean values")
        publish_salary = 1 if str(data.get("publish_salary_range")).lower() in ["true", "1"] else 0
        publish_website = 1 if str(data.get("publish_on_website")).lower() in ["true", "1"] else 0
        
        # Step 6: Parse dates
        frappe.logger().info("Step 6: Parsing dates")
        posted_on = data.get("posted_on") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        closes_on = data.get("closes_on") if data.get("closes_on") else None
        frappe.logger().info(f"Posted on: {posted_on}, Closes on: {closes_on}")
        
        # Step 7: Get optional fields
        frappe.logger().info("Step 7: Getting optional fields")
        location = data.get("location", "").strip() or None
        employment_type = data.get("employment_type", "").strip() or None
        department = data.get("department", "").strip() or None
        
        # Step 8: Create document dict
        frappe.logger().info("Step 8: Creating document dictionary")
        doc_dict = {
            "doctype": "Job Opening",
            "job_title": data.get("job_title"),
            "designation": data.get("designation"),
            "description": data.get("description", ""),
            "currency": data.get("currency", "INR"),
            "lower_range": lower_range_final,
            "upper_range": upper_range_final,
            "publish_salary_range": publish_salary,
            "company": data.get("company"),
            "employment_type": employment_type,
            "department": department,
            "location": location,
            "publish_on_website": publish_website,
            "posted_on": posted_on,
            "closes_on": closes_on,
            "status": status,
            "salary_per": data.get("salary_per", "Month")
        }
        
        frappe.logger().info(f"Document dict created: {json.dumps(doc_dict, indent=2, default=str)}")
        
        # Step 9: Create Job Opening document
        frappe.logger().info("Step 9: Creating frappe document")
        job_doc = frappe.get_doc(doc_dict)
        
        # Step 10: Insert document
        frappe.logger().info("Step 10: Inserting document")
        job_doc.insert(ignore_permissions=True, ignore_links=True)
        
        # Step 11: Commit
        frappe.logger().info("Step 11: Committing to database")
        frappe.db.commit()
        
        frappe.logger().info(f"=== SUCCESS: Job Opening {job_doc.name} created ===")
        
        return {
            "success": True,
            "message": f"Job Opening {job_doc.name} created successfully",
            "data": {
                "name": job_doc.name,
                "job_title": job_doc.job_title
            }
        }
        
    except Exception as e:
        frappe.logger().error(f"=== ERROR OCCURRED ===")
        frappe.logger().error(f"Error type: {type(e).__name__}")
        frappe.logger().error(f"Error message: {str(e)}")
        
        error_trace = frappe.get_traceback()
        frappe.logger().error(f"Full traceback: {error_trace}")
        
        frappe.db.rollback()
        frappe.log_error(title="Job Opening Creation Error", message=error_trace)
        
        return {
            "success": False,
            "message": f"Failed to create job opening: {str(e)}"
        }




# import frappe
# from datetime import datetime, timezone
# import json

# @frappe.whitelist(allow_guest=True)
# def create_job_opening():
#     """Your existing create function - keep as is"""
#     frappe.logger().info("=== CREATE JOB OPENING STARTED ===")
    
#     try:
#         data = frappe.form_dict
#         frappe.logger().info(f"Received data: {json.dumps(dict(data), indent=2)}")

#         if not data.get("job_title"):
#             frappe.logger().error("Validation failed: job_title missing")
#             return {"success": False, "message": "Job title is required"}
#         if not data.get("designation"):
#             frappe.logger().error("Validation failed: designation missing")
#             return {"success": False, "message": "Designation is required"}
#         if not data.get("company"):
#             frappe.logger().error("Validation failed: company missing")
#             return {"success": False, "message": "Company is required"}

#         status = data.get("status", "Open")
#         valid_statuses = ["Open", "Closed", "On Hold"]
#         if status not in valid_statuses:
#             return {"success": False, "message": f"Invalid status. Must be one of {', '.join(valid_statuses)}"}

#         lower_range_final = None
#         upper_range_final = None
        
#         lower_range_val = data.get("lower_range")
#         upper_range_val = data.get("upper_range")
        
#         frappe.logger().info(f"Lower range: {lower_range_val}, Upper range: {upper_range_val}")

#         if lower_range_val and upper_range_val:
#             try:
#                 lower = float(lower_range_val)
#                 upper = float(upper_range_val)
                
#                 if lower <= 0 or upper <= 0:
#                     return {"success": False, "message": "Salary ranges must be positive numbers"}
#                 if lower >= upper:
#                     return {"success": False, "message": "Minimum salary must be less than maximum salary"}
                
#                 lower_range_final = lower
#                 upper_range_final = upper
#                 frappe.logger().info(f"Salary range processed: {lower_range_final} - {upper_range_final}")
#             except (ValueError, TypeError) as e:
#                 frappe.logger().error(f"Salary conversion error: {str(e)}")
#                 return {"success": False, "message": "Salary ranges must be valid numbers"}

#         publish_salary = 1 if str(data.get("publish_salary_range")).lower() in ["true", "1"] else 0
#         publish_website = 1 if str(data.get("publish_on_website")).lower() in ["true", "1"] else 0
        
#         posted_on = data.get("posted_on") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
#         closes_on = data.get("closes_on") if data.get("closes_on") else None
#         frappe.logger().info(f"Posted on: {posted_on}, Closes on: {closes_on}")
        
#         location = data.get("location", "").strip() or None
#         employment_type = data.get("employment_type", "").strip() or None
#         department = data.get("department", "").strip() or None
        
#         doc_dict = {
#             "doctype": "Job Opening",
#             "job_title": data.get("job_title"),
#             "designation": data.get("designation"),
#             "description": data.get("description", ""),
#             "currency": data.get("currency", "INR"),
#             "lower_range": lower_range_final,
#             "upper_range": upper_range_final,
#             "publish_salary_range": publish_salary,
#             "company": data.get("company"),
#             "employment_type": employment_type,
#             "department": department,
#             "location": location,
#             "publish_on_website": publish_website,
#             "posted_on": posted_on,
#             "closes_on": closes_on,
#             "status": status,
#             "salary_per": data.get("salary_per", "Month")
#         }
        
#         frappe.logger().info(f"Document dict created: {json.dumps(doc_dict, indent=2, default=str)}")
        
#         job_doc = frappe.get_doc(doc_dict)
#         job_doc.insert(ignore_permissions=True, ignore_links=True)
#         frappe.db.commit()
        
#         frappe.logger().info(f"=== SUCCESS: Job Opening {job_doc.name} created ===")
        
#         return {
#             "success": True,
#             "message": f"Job Opening {job_doc.name} created successfully",
#             "data": {
#                 "name": job_doc.name,
#                 "job_title": job_doc.job_title
#             }
#         }
        
#     except Exception as e:
#         frappe.logger().error(f"=== ERROR OCCURRED ===")
#         frappe.logger().error(f"Error type: {type(e).__name__}")
#         frappe.logger().error(f"Error message: {str(e)}")
        
#         error_trace = frappe.get_traceback()
#         frappe.logger().error(f"Full traceback: {error_trace}")
        
#         frappe.db.rollback()
#         frappe.log_error(title="Job Opening Creation Error", message=error_trace)
        
#         return {
#             "success": False,
#             "message": f"Failed to create job opening: {str(e)}"
#         }


# # UPDATE FUNCTION - This is the one you need to add/fix
# @frappe.whitelist(methods=['POST'])
# def update_job_opening(job_name, data):
#     """
#     Update Job Opening
#     NOTE: Do NOT use allow_guest=True here - requires authentication
#     """
#     frappe.logger().info(f"=== UPDATE JOB OPENING STARTED for {job_name} ===")
    
#     try:
#         # Parse JSON if needed
#         if isinstance(data, str):
#             data = json.loads(data)
        
#         frappe.logger().info(f"Update data: {json.dumps(data, indent=2)}")
        
#         # Get the document - this checks permissions automatically
#         doc = frappe.get_doc("Job Opening", job_name)
        
#         # Update fields only if they exist in the data
#         if "job_title" in data:
#             doc.job_title = data["job_title"]
#         if "designation" in data:
#             doc.designation = data["designation"]
#         if "company" in data:
#             doc.company = data["company"]
#         if "location" in data:
#             doc.location = data["location"]
#         if "employment_type" in data:
#             doc.employment_type = data["employment_type"]
#         if "status" in data:
#             doc.status = data["status"]
#         if "posted_on" in data:
#             doc.posted_on = data["posted_on"]
#         if "closes_on" in data:
#             doc.closes_on = data["closes_on"]
#         if "lower_range" in data:
#             doc.lower_range = float(data["lower_range"]) if data["lower_range"] else None
#         if "upper_range" in data:
#             doc.upper_range = float(data["upper_range"]) if data["upper_range"] else None
#         if "currency" in data:
#             doc.currency = data["currency"]
#         if "salary_per" in data:
#             doc.salary_per = data["salary_per"]
#         if "description" in data:
#             doc.description = data["description"]
#         if "department" in data:
#             doc.department = data["department"]
#         if "publish_salary_range" in data:
#             doc.publish_salary_range = 1 if data["publish_salary_range"] else 0
#         if "publish_on_website" in data:
#             doc.publish_on_website = 1 if data["publish_on_website"] else 0
        
#         # Save the document
#         doc.save()
#         frappe.db.commit()
        
#         frappe.logger().info(f"=== SUCCESS: Job Opening {job_name} updated ===")
        
#         return {
#             "success": True,
#             "message": f"Job Opening {job_name} updated successfully",
#             "data": doc.as_dict()
#         }
        
#     except frappe.DoesNotExistError:
#         frappe.logger().error(f"Job Opening {job_name} not found")
#         frappe.db.rollback()
#         return {
#             "success": False,
#             "message": f"Job Opening {job_name} not found"
#         }
#     except frappe.PermissionError:
#         frappe.logger().error(f"Permission denied for {job_name}")
#         frappe.db.rollback()
#         return {
#             "success": False,
#             "message": "You don't have permission to update this Job Opening"
#         }
#     except Exception as e:
#         frappe.logger().error(f"=== ERROR OCCURRED ===")
#         frappe.logger().error(f"Error type: {type(e).__name__}")
#         frappe.logger().error(f"Error message: {str(e)}")
        
#         error_trace = frappe.get_traceback()
#         frappe.logger().error(f"Full traceback: {error_trace}")
        
#         frappe.db.rollback()
#         frappe.log_error(title="Job Opening Update Error", message=error_trace)
        
#         return {
#             "success": False,
#             "message": f"Failed to update job opening: {str(e)}"
#         }