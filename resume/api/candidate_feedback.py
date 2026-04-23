import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_candidate_feedback_list():
    """
    Fetch all Interview Feedback with combined Job Applicant and Job Opening data
    INCLUDING ALL CUSTOM FIELDS
    """
    try:
        # Fetch all Interview Feedback records using SQL with custom fields
        feedback_list = frappe.db.sql("""
            SELECT 
                name, interview, interviewer, result, 
                feedback, creation, modified,
                custom_candidate_name,
                custom_interview_date,
                custom_position_applied_for,
                custom_department,
                custom_location,
                custom_new_position,
                custom_replacement_position,
                custom_applicant_rating,
                custom_average_10_to_13,
                custom_good_14_to_18,
                custom_excellent_19_to_21,
                custom_not_shortlisted,
                custom__to_be__offered,
                custom_candidature_withdrawn,
                custom_no_show_for_interview,
                custom_not_as_qualified_as_others,
                custom_test_scores,
                custom_selected_for_other_position,
                custom_insufficient_skills,
                custom_offer_denied,
                custom_reference_check_unsatisfactory,
                custom_good_skillsexp_not_1st_choice,
                custom_poor_interview_ratings,
                custom_behavioural_attributes,
                custom_another_job,
                custom_changed_mind,
                custom_hourswork_schedule,
                custom_job_duties,
                custom_salary_too_low,
                custom_description
            FROM `tabInterview Feedback`
            ORDER BY creation DESC
        """, as_dict=True)
        
        if not feedback_list:
            return {
                "success": True,
                "data": [],
                "count": 0
            }
        
        result = []
        for feedback in feedback_list:
            # Initialize default values
            applicant_data = {
                "applicant_name": "N/A",
                "email_id": "N/A",
                "country": "N/A"
            }
            job_opening_data = {
                "job_title": "N/A",
                "location": "N/A"
            }
            interview_round = "N/A"
            skill_assessments = []
            avg_rating = 0
            
            try:
                # Fetch Interview details using SQL
                if feedback.get("interview"):
                    interview_data = frappe.db.sql("""
                        SELECT job_applicant, job_opening, interview_round
                        FROM `tabInterview`
                        WHERE name = %s
                    """, feedback.interview, as_dict=True)
                    
                    if interview_data and len(interview_data) > 0:
                        interview_doc = interview_data[0]
                        interview_round = interview_doc.get("interview_round") or "N/A"
                        
                        # Get Job Applicant data
                        if interview_doc.get("job_applicant"):
                            applicant_data_result = frappe.db.sql("""
                                SELECT applicant_name, email_id, country
                                FROM `tabJob Applicant`
                                WHERE name = %s
                            """, interview_doc["job_applicant"], as_dict=True)
                            
                            if applicant_data_result and len(applicant_data_result) > 0:
                                applicant = applicant_data_result[0]
                                applicant_data = {
                                    "applicant_name": applicant.get("applicant_name") or "N/A",
                                    "email_id": applicant.get("email_id") or "N/A",
                                    "country": applicant.get("country") or "N/A"
                                }
                        
                        # Get Job Opening data
                        if interview_doc.get("job_opening"):
                            job_opening_result = frappe.db.sql("""
                                SELECT job_title, location
                                FROM `tabJob Opening`
                                WHERE name = %s
                            """, interview_doc["job_opening"], as_dict=True)
                            
                            if job_opening_result and len(job_opening_result) > 0:
                                job_opening = job_opening_result[0]
                                job_opening_data = {
                                    "job_title": job_opening.get("job_title") or "N/A",
                                    "location": job_opening.get("location") or "N/A"
                                }
                
                # Try to fetch skill assessments
                try:
                    doc = frappe.get_doc("Interview Feedback", feedback.name)
                    meta = frappe.get_meta("Interview Feedback")
                    
                    # Find child table field
                    child_table_fieldname = None
                    for field in meta.fields:
                        if field.fieldtype == "Table" and "skill" in field.fieldname.lower():
                            child_table_fieldname = field.fieldname
                            break
                    
                    if child_table_fieldname and hasattr(doc, child_table_fieldname):
                        skills = getattr(doc, child_table_fieldname)
                        if skills:
                            skill_assessments = []
                            total_rating = 0
                            for skill in skills:
                                # Convert Frappe rating (0-1) to 5-star rating
                                frappe_rating = float(skill.get("rating", 0))
                                star_rating = int(frappe_rating * 5)
                                
                                skill_data = {
                                    "skill": skill.get("skill", ""),
                                    "rating": star_rating
                                }
                                skill_assessments.append(skill_data)
                                total_rating += star_rating
                            
                            if len(skill_assessments) > 0:
                                avg_rating = round(total_rating / len(skill_assessments), 1)
                except:
                    skill_assessments = []
                    avg_rating = 0
                
            except Exception as e:
                frappe.log_error(f"Error processing feedback {feedback.name}: {str(e)}")
            
            # Parse checkbox fields into arrays
            final_score_recommendation = []
            if feedback.get("custom_average_10_to_13"):
                final_score_recommendation.append("Average (10 to 13)")
            if feedback.get("custom_good_14_to_18"):
                final_score_recommendation.append("Good (14 to 18)")
            if feedback.get("custom_excellent_19_to_21"):
                final_score_recommendation.append("Excellent (19 to 21)")
            if feedback.get("custom_not_shortlisted"):
                final_score_recommendation.append("Not Shortlisted")
            if feedback.get("custom__to_be__offered"):
                final_score_recommendation.append("To be Offered")
            if feedback.get("custom_candidature_withdrawn"):
                final_score_recommendation.append("Candidature Withdrawn")
            
            not_shortlisted_reason = []
            if feedback.get("custom_no_show_for_interview"):
                not_shortlisted_reason.append("No Show for interview")
            if feedback.get("custom_not_as_qualified_as_others"):
                not_shortlisted_reason.append("Not as qualified as others")
            if feedback.get("custom_test_scores"):
                not_shortlisted_reason.append("Test Scores")
            if feedback.get("custom_selected_for_other_position"):
                not_shortlisted_reason.append("Selected for other position")
            if feedback.get("custom_insufficient_skills"):
                not_shortlisted_reason.append("Insufficient Skills")
            if feedback.get("custom_offer_denied"):
                not_shortlisted_reason.append("Offer Denied")
            if feedback.get("custom_reference_check_unsatisfactory"):
                not_shortlisted_reason.append("Reference Check Unsatisfactory")
            if feedback.get("custom_good_skillsexp_not_1st_choice"):
                not_shortlisted_reason.append("Good Skills/Exp, not 1st choice")
            if feedback.get("custom_poor_interview_ratings"):
                not_shortlisted_reason.append("Poor Interview Ratings")
            if feedback.get("custom_behavioural_attributes"):
                not_shortlisted_reason.append("Behavioural Attributes")
            
            withdrawn_reason = []
            if feedback.get("custom_another_job"):
                withdrawn_reason.append("Another Job")
            if feedback.get("custom_changed_mind"):
                withdrawn_reason.append("Changed Mind")
            if feedback.get("custom_hourswork_schedule"):
                withdrawn_reason.append("Hours/Work Schedule")
            if feedback.get("custom_job_duties"):
                withdrawn_reason.append("Job Duties")
            if feedback.get("custom_salary_too_low"):
                withdrawn_reason.append("Salary too low")
            
            # Combine all data
            result.append({
                "name": feedback.name,
                "interview": feedback.interview or "N/A",
                "interviewer": feedback.interviewer or "N/A",
                "result": feedback.result or "N/A",
                "feedback": feedback.feedback or "",
                "interview_round": interview_round,
                "creation": str(feedback.creation) if feedback.creation else "",
                "modified": str(feedback.modified) if feedback.modified else "",
                "applicant": applicant_data,
                "job_opening": job_opening_data,
                "skill_assessments": skill_assessments,
                "average_rating": avg_rating,
                "total_skills": len(skill_assessments),
                # Custom fields
                "candidate_name": feedback.get("custom_candidate_name") or "",
                "interview_date": str(feedback.get("custom_interview_date")) if feedback.get("custom_interview_date") else "",
                "position_applied_for": feedback.get("custom_position_applied_for") or "",
                "department": feedback.get("custom_department") or "",
                "location": feedback.get("custom_location") or "",
                "new_position": feedback.get("custom_new_position") or "",
                "replacement_position": feedback.get("custom_replacement_position") or "",
                "applicant_rating": feedback.get("custom_applicant_rating") or "",
                "final_score_recommendation": final_score_recommendation,
                "not_shortlisted_reason": not_shortlisted_reason,
                "withdrawn_reason": withdrawn_reason,
                "remarks": feedback.get("custom_description") or ""
            })
        
        return {
            "success": True,
            "data": result,
            "count": len(result)
        }
        
    except Exception as e:
        error_msg = str(e)
        frappe.log_error(frappe.get_traceback(), "Get Candidate Feedback List Error")
        return {
            "success": False,
            "error": error_msg,
            "data": [],
            "count": 0
        }

@frappe.whitelist()
def get_candidate_feedback_details(feedback_name):
    """
    Fetch detailed information for a specific candidate feedback
    """
    try:
        # Fetch the feedback document
        feedback = frappe.get_doc("Interview Feedback", feedback_name)
        
        # Fetch Job Applicant details
        applicant_data = {}
        
        # Fetch Job Opening details
        job_opening_data = {}
        if feedback.interview:
            try:
                interview = frappe.get_doc("Interview", feedback.interview)
                
                # Get applicant
                if interview.get("job_applicant"):
                    try:
                        applicant = frappe.get_doc("Job Applicant", interview.job_applicant)
                        applicant_data = {
                            "name": applicant.name,
                            "applicant_name": applicant.applicant_name,
                            "email_id": applicant.email_id,
                            "country": applicant.get("country") or "",
                            "phone_number": applicant.get("phone_number") or "",
                            "status": applicant.status,
                            "total_experience": applicant.get("total_experience") or "",
                            "resume_attachment": applicant.get("resume_attachment") or ""
                        }
                    except:
                        pass
                
                # Get job opening
                if interview.get("job_opening"):
                    try:
                        job_opening = frappe.get_doc("Job Opening", interview.job_opening)
                        job_opening_data = {
                            "name": job_opening.name,
                            "job_title": job_opening.job_title,
                            "location": job_opening.get("location") or "",
                            "department": job_opening.get("department") or "",
                            "designation": job_opening.get("designation") or "",
                            "description": job_opening.get("description") or ""
                        }
                    except:
                        pass
            except:
                pass
        
        # Fetch skill assessments
        skill_assessments = []
        try:
            meta = frappe.get_meta("Interview Feedback")
            child_table_fieldname = None
            
            for field in meta.fields:
                if field.fieldtype == "Table" and "skill" in field.fieldname.lower():
                    child_table_fieldname = field.fieldname
                    break
            
            if child_table_fieldname and hasattr(feedback, child_table_fieldname):
                skills = getattr(feedback, child_table_fieldname)
                if skills:
                    for skill in skills:
                        frappe_rating = float(skill.get("rating", 0))
                        star_rating = int(frappe_rating * 5)
                        skill_assessments.append({
                            "skill": skill.get("skill", ""),
                            "rating": star_rating
                        })
        except:
            pass
        
        # Fetch interviewer details
        interviewer_data = {}
        if feedback.interviewer:
            try:
                interviewer = frappe.get_doc("User", feedback.interviewer)
                interviewer_data = {
                    "name": interviewer.name,
                    "full_name": interviewer.full_name,
                    "email": interviewer.email
                }
            except:
                pass
        
        return {
            "success": True,
            "data": {
                "feedback": {
                    "name": feedback.name,
                    "interview": feedback.interview,
                    "interviewer": feedback.interviewer,
                    "result": feedback.result,
                    "feedback": feedback.feedback or "",
                    "creation": str(feedback.creation),
                    "modified": str(feedback.modified)
                },
                "applicant": applicant_data,
                "job_opening": job_opening_data,
                "skill_assessments": skill_assessments,
                "interviewer_details": interviewer_data
            }
        }
        
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "error": "Feedback record not found"
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Feedback Details Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_feedback_statistics():
    """
    Get statistics for feedback dashboard
    """
    try:
        total_feedback = frappe.db.count("Interview Feedback")
        
        cleared_count = frappe.db.count("Interview Feedback", {"result": "Cleared"})
        rejected_count = frappe.db.count("Interview Feedback", {"result": "Rejected"})
        
        # Get recent feedback
        recent_feedback = frappe.get_all(
            "Interview Feedback",
            fields=["name", "result", "creation"],
            order_by="creation desc",
            limit=5
        )
        
        return {
            "success": True,
            "data": {
                "total_feedback": total_feedback,
                "cleared": cleared_count,
                "rejected": rejected_count,
                "recent_feedback": recent_feedback
            }
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Feedback Statistics Error")
        return {
            "success": False,
            "error": str(e)
        }
