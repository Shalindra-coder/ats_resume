import frappe
from datetime import datetime
import json

@frappe.whitelist(allow_guest=True)
def create_interview_feedback():
    """Create a new interview feedback"""
    try:
        data = frappe.form_dict
        frappe.log_error("Received interview feedback data: {data}".format(data=json.dumps(dict(data), indent=2)), "Interview Feedback Debug")

        # Define required fields
        required_fields = ["interview", "interviewer", "result"]
        for field in required_fields:
            if not data.get(field):
                frappe.throw(f"{field} is required")

        # Get valid results from the doctype field options
        try:
            meta = frappe.get_meta("Interview Feedback")
            result_field = None
            for field in meta.fields:
                if field.fieldname == "result":
                    result_field = field
                    break
            
            if result_field and result_field.options:
                valid_results = [opt.strip() for opt in result_field.options.split('\n') if opt.strip()]
            else:
                valid_results = ["Cleared", "Rejected", "On Hold", "Pending Review"]
        except:
            valid_results = ["Cleared", "Rejected", "On Hold", "Pending Review"]

        # Validate result
        result = data.get("result")
        
        if not result or result not in valid_results:
            frappe.throw(f"Invalid or missing result. Must be one of {', '.join(valid_results)}")

        # Validate designation if provided
        position_applied_for = data.get("position_applied_for")
        if position_applied_for:
            if not frappe.db.exists("Designation", position_applied_for):
                frappe.log_error(f"Designation '{position_applied_for}' does not exist", "Invalid Designation")
                # Set to None if designation doesn't exist
                position_applied_for = None

        # Parse checkbox arrays from JSON strings
        final_score_recommendation = []
        not_shortlisted_reason = []
        withdrawn_reason = []
        
        if data.get("final_score_recommendation"):
            final_score_recommendation = json.loads(data.final_score_recommendation) if isinstance(data.final_score_recommendation, str) else data.final_score_recommendation
            
        if data.get("not_shortlisted_reason"):
            not_shortlisted_reason = json.loads(data.not_shortlisted_reason) if isinstance(data.not_shortlisted_reason, str) else data.not_shortlisted_reason
            
        if data.get("withdrawn_reason"):
            withdrawn_reason = json.loads(data.withdrawn_reason) if isinstance(data.withdrawn_reason, str) else data.withdrawn_reason
        
        # Map options to field names for Final Score
        final_score_map = {
            "Average (10 to 13)": "custom_average_10_to_13",
            "Good (14 to 18)": "custom_good_14_to_18",
            "Excellent (19 to 21)": "custom_excellent_19_to_21",
            "Not Shortlisted": "custom_not_shortlisted",
            "To be Offered": "custom__to_be__offered",
            "Candidature Withdrawn": "custom_candidature_withdrawn"
        }
        
        # Map options to field names for Not Shortlisted
        not_shortlisted_map = {
            "No Show for interview": "custom_no_show_for_interview",
            "Not as qualified as others": "custom_not_as_qualified_as_others",
            "Test Scores": "custom_test_scores",
            "Selected for other position": "custom_selected_for_other_position",
            "Insufficient Skills": "custom_insufficient_skills",
            "Offer Denied": "custom_offer_denied",
            "Reference Check Unsatisfactory": "custom_reference_check_unsatisfactory",
            "Good Skills/Exp, not 1st choice": "custom_good_skillsexp_not_1st_choice",
            "Poor Interview Ratings": "custom_poor_interview_ratings",
            "Behavioural Attributes": "custom_behavioural_attributes"
        }
        
        # Map options to field names for Withdrawn Reason
        withdrawn_map = {
            "Another Job": "custom_another_job",
            "Changed Mind": "custom_changed_mind",
            "Hours/Work Schedule": "custom_hourswork_schedule",
            "Job Duties": "custom_job_duties",
            "Salary too low": "custom_salary_too_low"
        }
        
        # Create the Interview Feedback document
        feedback_doc = frappe.get_doc({
            "doctype": "Interview Feedback",
            "interview": data.interview,
            "interviewer": data.interviewer,
            "result": result,
            "feedback": data.get("feedback"),
            "custom_candidate_name": data.get("candidate_name"),
            "custom_interview_date": data.get("interview_date"),
            "custom_position_applied_for": data.get("position_applied_for"),
            "custom_department": data.get("department"),
            "custom_location": data.get("location"),
            "custom_new_position": data.get("new_position"),
            "custom_replacement_position": data.get("replacement_position"),
            "custom_applicant_rating": data.get("applicant_rating"),
            "custom_description": data.get("remarks"),
        })
        
        # Set Final Score checkboxes
        for option in final_score_recommendation:
            field_name = final_score_map.get(option)
            if field_name:
                feedback_doc.set(field_name, 1)
        
        # Set Not Shortlisted checkboxes
        for option in not_shortlisted_reason:
            field_name = not_shortlisted_map.get(option)
            if field_name:
                feedback_doc.set(field_name, 1)
        
        # Set Withdrawn Reason checkboxes
        for option in withdrawn_reason:
            field_name = withdrawn_map.get(option)
            if field_name:
                feedback_doc.set(field_name, 1)
        
        # Add skill assessments if provided
        if data.get("skill_assessments"):
            skill_assessments = json.loads(data.skill_assessments) if isinstance(data.skill_assessments, str) else data.skill_assessments
            
            meta = frappe.get_meta("Interview Feedback")
            child_table_fieldname = None
            
            for field in meta.fields:
                if field.fieldtype == "Table" and "skill" in field.fieldname.lower():
                    child_table_fieldname = field.fieldname
                    break
            
            if child_table_fieldname:
                for skill in skill_assessments:
                    if skill.get("skill") and skill.get("rating"):
                        skill_name = str(skill.get("skill")).strip()
                        rating_value = int(skill.get("rating"))
                        
                        if not frappe.db.exists("Skill", skill_name):
                            frappe.throw(f"Skill '{skill_name}' does not exist. Please create it first or select from available skills.")
                        
                        frappe_rating = rating_value / 5.0
                        
                        feedback_doc.append(child_table_fieldname, {
                            "skill": skill_name,
                            "rating": frappe_rating
                        })
        
        feedback_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.log_error(f"Successfully created Interview Feedback: {feedback_doc.name}", "Interview Feedback Success")
        
        return {
            "message": f"Interview Feedback {feedback_doc.name} created successfully.",
            "name": feedback_doc.name,
            "doc": feedback_doc.as_dict()
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interview Feedback Creation Failed")
        frappe.db.rollback()
        frappe.throw(f"Failed to create interview feedback: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_interview_feedbacks():
    """Get list of all interview feedbacks"""
    try:
        feedbacks = frappe.db.sql("""
            SELECT 
                name, interview, interviewer, result, 
                creation, modified, owner, docstatus
            FROM `tabInterview Feedback`
            ORDER BY creation DESC
        """, as_dict=True)
        
        result = []
        for feedback in feedbacks:
            try:
                doc = frappe.get_doc("Interview Feedback", feedback.name)
                
                feedback_data = {
                    "name": doc.name,
                    "interview": doc.interview,
                    "interviewer": doc.interviewer,
                    "result": doc.result,
                    "creation": str(doc.creation),
                    "modified": str(doc.modified),
                    "owner": doc.owner,
                    "status": "Submitted" if doc.docstatus == 1 else "Draft",
                    "candidate_name": doc.get("custom_candidate_name"),
                    "position_applied_for": doc.get("custom_position_applied_for"),
                    "department": doc.get("custom_department"),
                    "interview_date": str(doc.get("custom_interview_date")) if doc.get("custom_interview_date") else None,
                    "feedback": doc.get("feedback"),
                    "skills_count": 0
                }
                
                if doc.interview:
                    try:
                        interview = frappe.get_doc("Interview", doc.interview)
                        feedback_data["interview_round"] = interview.get("interview_round")
                        feedback_data["job_applicant"] = interview.get("job_applicant")
                        
                        if feedback_data.get("job_applicant"):
                            try:
                                applicant = frappe.get_doc("Job Applicant", feedback_data["job_applicant"])
                                feedback_data["applicant_name"] = applicant.applicant_name
                            except:
                                pass
                    except:
                        pass
                
                result.append(feedback_data)
            except Exception as e:
                frappe.log_error(f"Error fetching feedback {feedback.name}: {str(e)}")
                continue
        
        return {
            "message": "Interview feedbacks fetched successfully",
            "data": result,
            "count": len(result)
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interview Feedbacks Fetch Failed")
        return {
            "message": f"Failed to fetch interview feedbacks: {str(e)}",
            "data": [],
            "count": 0
        }


@frappe.whitelist(allow_guest=True)
def delete_interview_feedback(name):
    """Delete an interview feedback"""
    try:
        if not name:
            frappe.throw("Feedback name is required")
        
        frappe.delete_doc("Interview Feedback", name, ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "message": f"Interview Feedback {name} deleted successfully"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interview Feedback Deletion Failed")
        frappe.db.rollback()
        frappe.throw(f"Failed to delete interview feedback: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_skills():
    """Get list of all skills"""
    try:
        skills = frappe.get_all("Skill", fields=["name", "skill_name"], order_by="name asc")
        return {
            "message": "Skills fetched successfully",
            "data": [skill.name for skill in skills]
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Skills Fetch Failed")
        return {"message": f"Failed to fetch skills: {str(e)}", "data": []}


@frappe.whitelist(allow_guest=True)
def get_applicant_rating_options():
    """Get applicant rating options"""
    try:
        meta = frappe.get_meta("Interview Feedback")
        for field in meta.fields:
            if field.fieldname == "custom_applicant_rating":
                if field.options:
                    return {
                        "message": "Success",
                        "data": [opt.strip() for opt in field.options.split('\n') if opt.strip()]
                    }
        
        return {
            "message": "Using defaults",
            "data": ["Unsatisfactory", "Marginal", "Satisfactory", "Superior"]
        }
    except:
        return {
            "message": "Using defaults",
            "data": ["Unsatisfactory", "Marginal", "Satisfactory", "Superior"]
        }


@frappe.whitelist(allow_guest=True)
def get_department_options():
    """Get department options"""
    try:
        departments = frappe.get_all("Department", fields=["name"], order_by="name asc")
        if departments:
            return {
                "message": "Success",
                "data": [dept.name for dept in departments]
            }
        return {
            "message": "Using defaults",
            "data": ["Accounts", "Human Resources", "Marketing", "Operations"]
        }
    except:
        return {
            "message": "Using defaults",
            "data": ["Accounts", "Human Resources", "Marketing", "Operations"]
        }


@frappe.whitelist(allow_guest=True)
def get_location_options():
    """Get location options"""
    try:
        locations = frappe.get_all("Location", fields=["name"], order_by="name asc")
        if locations:
            return {"message": "Success", "data": [loc.name for loc in locations]}
    except:
        pass
    
    return {"message": "Using defaults", "data": ["Borivali,Mumbai"]}


@frappe.whitelist(allow_guest=True)
def get_designation_options():
    """Get designation options from Designation doctype"""
    try:
        # Fetch all designations
        designations = frappe.get_all(
            "Designation",
            fields=["name"],
            order_by="name asc"
        )
        
        if designations and len(designations) > 0:
            designation_list = [d.name for d in designations]
            return {
                "message": "Success",
                "data": designation_list
            }
        
        # If no designations found, return empty array
        return {
            "message": "No designations found",
            "data": []
        }
    except Exception as e:
        frappe.log_error(f"Error fetching designations: {str(e)}\n{frappe.get_traceback()}", "Designation Error")
        # Return empty array on error so frontend doesn't break
        return {
            "message": f"Error: {str(e)}",
            "data": []
        }


@frappe.whitelist(allow_guest=True)
def get_interviews():
    """Get list of interviews"""
    try:
        interviews = frappe.get_all("Interview", fields=["name"], order_by="creation desc")
        
        result = []
        for interview_name in interviews:
            try:
                doc = frappe.get_doc("Interview", interview_name.name)
                interview_data = {
                    "name": doc.name,
                    "job_applicant": doc.get("job_applicant"),
                    "interview_round": doc.get("interview_round"),
                    "scheduled_on": doc.get("scheduled_on"),
                    "status": doc.get("status")
                }
                
                if interview_data.get("job_applicant"):
                    try:
                        applicant = frappe.get_doc("Job Applicant", interview_data["job_applicant"])
                        interview_data["applicant_name"] = applicant.applicant_name
                    except:
                        pass
                
                result.append(interview_data)
            except:
                continue
        
        return {"message": "Success", "data": result}
    except Exception as e:
        return {"message": f"Error: {str(e)}", "data": []}


@frappe.whitelist(allow_guest=True)
def get_interviewers():
    """Get list of interviewers"""
    try:
        users = frappe.get_all(
            "User",
            fields=["name", "email", "full_name", "first_name"],
            filters={"enabled": 1, "name": ["not in", ["Administrator", "Guest"]]},
            order_by="name"
        )
        
        result = []
        for user in users:
            result.append({
                "name": user.name,
                "full_name": user.full_name or user.first_name or user.name,
                "email": user.email
            })
        
        return {"message": "Success", "data": result}
    except Exception as e:
        return {"message": f"Error: {str(e)}", "data": []}


@frappe.whitelist(allow_guest=True)
def get_result_options():
    """Get result options"""
    try:
        meta = frappe.get_meta("Interview Feedback")
        for field in meta.fields:
            if field.fieldname == "result" and field.options:
                return {
                    "message": "Success",
                    "data": [opt.strip() for opt in field.options.split('\n') if opt.strip()]
                }
        return {"message": "Using defaults", "data": ["Cleared", "Rejected", "On Hold"]}
    except:
        return {"message": "Using defaults", "data": ["Cleared", "Rejected", "On Hold"]}


@frappe.whitelist(allow_guest=True)
def get_final_score_options():
    """Get final score options"""
    return {
        "message": "Success",
        "data": [
            "Average (10 to 13)", "Good (14 to 18)", "Excellent (19 to 21)",
            "Not Shortlisted", "To be Offered", "Candidature Withdrawn"
        ]
    }


@frappe.whitelist(allow_guest=True)
def get_not_shortlisted_options():
    """Get not shortlisted options"""
    return {
        "message": "Success",
        "data": [
            "No Show for interview", "Not as qualified as others", "Test Scores",
            "Selected for other position", "Insufficient Skills", "Offer Denied",
            "Reference Check Unsatisfactory", "Good Skills/Exp, not 1st choice",
            "Poor Interview Ratings", "Behavioural Attributes"
        ]
    }


@frappe.whitelist(allow_guest=True)
def get_withdrawn_reason_options():
    """Get withdrawn reason options"""
    return {
        "message": "Success",
        "data": [
            "Another Job", "Changed Mind", "Hours/Work Schedule",
            "Job Duties", "Salary too low"
        ]
    }


@frappe.whitelist(allow_guest=True)
def get_job_applicant_details(job_applicant):
    """Get job applicant details including designation, department, and location from Job Opening"""
    try:
        if not job_applicant:
            return {"message": "No job applicant provided", "data": None}
        
        # Fetch job applicant details
        applicant = frappe.get_doc("Job Applicant", job_applicant)
        
        result = {
            "name": applicant.name,
            "applicant_name": applicant.applicant_name,
            "email_id": applicant.email_id,
            "designation": None,
            "department": None,
            "location": None
        }
        
        # Get details from linked Job Opening
        job_opening_name = None
        
        # First try to get from job_opening field directly
        if hasattr(applicant, 'job_opening') and applicant.job_opening:
            job_opening_name = applicant.job_opening
        
        # Also try job_title field which might contain the Job Opening reference
        if not job_opening_name and hasattr(applicant, 'job_title') and applicant.job_title:
            # Check if job_title is actually a Job Opening ID
            if frappe.db.exists("Job Opening", applicant.job_title):
                job_opening_name = applicant.job_title
        
        # If Job Opening is found, fetch all required details
        if job_opening_name:
            try:
                job_opening = frappe.get_doc("Job Opening", job_opening_name)
                
                # Get designation from Job Opening
                if hasattr(job_opening, 'designation') and job_opening.designation:
                    result["designation"] = job_opening.designation
                elif hasattr(job_opening, 'job_title') and job_opening.job_title:
                    result["designation"] = job_opening.job_title
                
                # Get department from Job Opening
                if hasattr(job_opening, 'department') and job_opening.department:
                    result["department"] = job_opening.department
                
                # Get location from Job Opening
                if hasattr(job_opening, 'location') and job_opening.location:
                    result["location"] = job_opening.location
                    
            except Exception as e:
                pass  # Job Opening not found or error accessing it
        
        # Return the result (don't log to avoid title length error)
        return {"message": "Success", "data": result}
        
    except Exception as e:
        # Return error without detailed logging to avoid title length issues
        return {"message": f"Error: {str(e)}", "data": None}


@frappe.whitelist(allow_guest=True)
def get_candidate_feedback_list():
    """Get candidate feedback list - SIMPLE VERSION"""
    try:
        feedback_list = frappe.db.sql("""
            SELECT name, interview, interviewer, result, feedback, creation, modified
            FROM `tabInterview Feedback`
            ORDER BY creation DESC
        """, as_dict=True)
        
        result = []
        for feedback in feedback_list:
            try:
                feedback_data = {
                    "name": feedback.name,
                    "interview": feedback.interview,
                    "interviewer": feedback.interviewer,
                    "result": feedback.result,
                    "feedback": feedback.feedback,
                    "creation": str(feedback.creation),
                    "modified": str(feedback.modified),
                }
                
                # Get interview details
                try:
                    interview_data = frappe.db.sql("""
                        SELECT job_applicant, job_opening, interview_round
                        FROM `tabInterview`
                        WHERE name = %s
                    """, feedback.interview, as_dict=True)
                    
                    if interview_data and len(interview_data) > 0:
                        interview = interview_data[0]
                        feedback_data["interview_round"] = interview.get("interview_round")
                        
                        if interview.get("job_applicant"):
                            applicant_data = frappe.db.sql("""
                                SELECT applicant_name, email_id, country
                                FROM `tabJob Applicant`
                                WHERE name = %s
                            """, interview["job_applicant"], as_dict=True)
                            
                            if applicant_data:
                                feedback_data["applicant"] = applicant_data[0]
                        
                        if interview.get("job_opening"):
                            job_data = frappe.db.sql("""
                                SELECT job_title, location
                                FROM `tabJob Opening`
                                WHERE name = %s
                            """, interview["job_opening"], as_dict=True)
                            
                            if job_data:
                                feedback_data["job_opening"] = job_data[0]
                except:
                    pass
                
                result.append(feedback_data)
            except:
                continue
        
        return {"message": "Success", "data": result, "count": len(result)}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Candidate Feedback List Failed")
        return {"message": f"Error: {str(e)}", "data": [], "count": 0}
        
