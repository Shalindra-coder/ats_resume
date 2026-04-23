# import frappe
# from datetime import datetime
# import json

# # Define recruitment stages
# RECRUITMENT_STAGES = [
#     {'id': 'interview', 'label': 'Interview', 'order': 1},
#     {'id': 'feedback', 'label': 'Candidate Feedback', 'order': 2},
#     {'id': 'document_verification', 'label': 'Document Verification', 'order': 3},
#     {'id': 'offer_letter', 'label': 'Offer Letter', 'order': 4},
#     {'id': 'appointment_letter', 'label': 'Appointment Letter', 'order': 5},
# ]

# @frappe.whitelist(allow_guest=True)
# def get_all_candidates():
#     """Get list of all job applicants with complete details including stage tracking"""
#     try:
#         candidates = frappe.get_all(
#             "Job Applicant",
#             fields=[
#                 "name",
#                 "applicant_name",
#                 "email_id",
#                 "phone_number",
#                 "job_title",
#                 "designation",
#                 "status",
#                 "country",
#                 "location",
#                 "address",
#                 "source",
#                 "notes",
#                 "resume_link",
#                 "cover_letter",
#                 "creation",
#                 "modified",
#                 "resume_score",
#                 "custom_recruitment_stage"
#             ],
#             order_by="creation desc"
#         )
        
#         # Enrich with stage statuses
#         for candidate in candidates:
#             candidate["stage_statuses"] = get_candidate_stage_statuses(candidate.name)
        
#         frappe.log(f"Fetched {len(candidates)} candidates with stage tracking")
        
#         return {
#             "message": "Candidates fetched successfully",
#             "data": candidates,
#             "total": len(candidates)
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Candidates Fetch Failed")
#         frappe.throw(f"Failed to fetch candidates: {str(e)}")


# def get_candidate_stage_statuses(candidate_id):
#     """Get stage statuses for a candidate"""
#     statuses = []
    
#     try:
#         # Stage 1: Interview
#         interviews = frappe.get_all(
#             "Interview",
#             filters={"job_applicant": candidate_id},
#             fields=["status", "scheduled_on", "from_time", "to_time"],
#             order_by="scheduled_on desc"
#         )
        
#         if interviews:
#             latest_interview = interviews[0]
#             if latest_interview.status in ["Completed", "Cleared"]:
#                 statuses.append({
#                     "stage_id": "interview",
#                     "status": "completed",
#                     "completed_date": latest_interview.scheduled_on,
#                     "notes": f"Interview status: {latest_interview.status}"
#                 })
#             elif latest_interview.status == "Rejected":
#                 statuses.append({
#                     "stage_id": "interview",
#                     "status": "rejected",
#                     "completed_date": latest_interview.scheduled_on,
#                     "notes": "Interview rejected"
#                 })
#             else:
#                 statuses.append({
#                     "stage_id": "interview",
#                     "status": "in_progress",
#                     "notes": f"Interview scheduled for {latest_interview.scheduled_on}"
#                 })
#         else:
#             statuses.append({
#                 "stage_id": "interview",
#                 "status": "pending",
#                 "notes": "No interview scheduled yet"
#             })
        
#         # Stage 2: Feedback
#         feedbacks = frappe.get_all(
#             "Interview Feedback",
#             filters={"job_applicant": candidate_id},
#             fields=["creation", "result"],
#             order_by="creation desc"
#         )
        
#         if feedbacks:
#             latest_feedback = feedbacks[0]
#             statuses.append({
#                 "stage_id": "feedback",
#                 "status": "completed",
#                 "completed_date": latest_feedback.creation,
#                 "notes": f"Feedback result: {latest_feedback.get('result', 'Submitted')}"
#             })
#         else:
#             # Only mark as pending if interview is completed
#             interview_completed = any(s for s in statuses if s["stage_id"] == "interview" and s["status"] == "completed")
#             statuses.append({
#                 "stage_id": "feedback",
#                 "status": "in_progress" if interview_completed else "pending",
#                 "notes": "Awaiting feedback" if interview_completed else "Complete interview first"
#             })
        
#         # Stage 3: Document Verification
#         documents = frappe.get_all(
#             "Applicant Document",
#             filters={"applicant_name": candidate_id},
#             fields=["name", "creation", "aadhar_card", "pan", "education", "experience", "bank_details"],
#             limit=1
#         )
        
#         if documents:
#             doc = documents[0]
#             mandatory_docs = ['aadhar_card', 'pan', 'education', 'experience', 'bank_details']
#             uploaded_count = sum(1 for field in mandatory_docs if doc.get(field))
            
#             if uploaded_count == len(mandatory_docs):
#                 statuses.append({
#                     "stage_id": "document_verification",
#                     "status": "completed",
#                     "completed_date": doc.creation,
#                     "notes": "All mandatory documents uploaded and verified"
#                 })
#             else:
#                 statuses.append({
#                     "stage_id": "document_verification",
#                     "status": "in_progress",
#                     "notes": f"{uploaded_count}/{len(mandatory_docs)} mandatory documents uploaded"
#                 })
#         else:
#             feedback_completed = any(s for s in statuses if s["stage_id"] == "feedback" and s["status"] == "completed")
#             statuses.append({
#                 "stage_id": "document_verification",
#                 "status": "in_progress" if feedback_completed else "pending",
#                 "notes": "No documents uploaded yet" if feedback_completed else "Complete previous stages first"
#             })
        
#         # Stage 4: Offer Letter
#         offers = frappe.get_all(
#             "Job Offer",
#             filters={"job_applicant": candidate_id},
#             fields=["name", "creation", "status", "offer_date"],
#             order_by="creation desc",
#             limit=1
#         )
        
#         if offers:
#             offer = offers[0]
#             statuses.append({
#                 "stage_id": "offer_letter",
#                 "status": "completed",
#                 "completed_date": offer.offer_date or offer.creation,
#                 "notes": f"Offer status: {offer.status}"
#             })
#         else:
#             doc_completed = any(s for s in statuses if s["stage_id"] == "document_verification" and s["status"] == "completed")
#             statuses.append({
#                 "stage_id": "offer_letter",
#                 "status": "in_progress" if doc_completed else "pending",
#                 "notes": "Ready to send offer" if doc_completed else "Complete document verification first"
#             })
        
#         # Stage 5: Appointment Letter
#         appointments = frappe.get_all(
#             "Appointment Letter",
#             filters={"applicant_name": candidate_id},
#             fields=["name", "creation", "status", "date_of_joining"],
#             limit=1
#         )
        
#         if appointments:
#             appointment = appointments[0]
#             statuses.append({
#                 "stage_id": "appointment_letter",
#                 "status": "completed",
#                 "completed_date": appointment.date_of_joining or appointment.creation,
#                 "notes": f"Joining date: {appointment.date_of_joining}"
#             })
#         else:
#             offer_completed = any(s for s in statuses if s["stage_id"] == "offer_letter" and s["status"] == "completed")
#             statuses.append({
#                 "stage_id": "appointment_letter",
#                 "status": "in_progress" if offer_completed else "pending",
#                 "notes": "Ready to send appointment letter" if offer_completed else "Complete offer letter first"
#             })
        
#     except Exception as e:
#         frappe.log_error(f"Error getting stage statuses for {candidate_id}: {str(e)}")
    
#     return statuses


# @frappe.whitelist(allow_guest=True)
# def get_candidate_details(candidate_id):
#     """Get detailed information about a specific candidate including stage tracking"""
#     try:
#         if not candidate_id:
#             frappe.throw("Candidate ID is required")
        
#         candidate = frappe.get_doc("Job Applicant", candidate_id)
        
#         # Get related interviews
#         interviews = frappe.get_all(
#             "Interview",
#             filters={"job_applicant": candidate_id},
#             fields=[
#                 "name",
#                 "interview_round",
#                 "scheduled_on",
#                 "from_time",
#                 "to_time",
#                 "status",
#                 "google_meet",
#                 "custom_location",
#                 "notes"
#             ],
#             order_by="scheduled_on desc"
#         )
        
#         # Get stage statuses
#         stage_statuses = get_candidate_stage_statuses(candidate_id)
        
#         candidate_dict = candidate.as_dict()
#         candidate_dict["interviews"] = interviews
#         candidate_dict["stage_statuses"] = stage_statuses
        
#         return {
#             "message": "Candidate details fetched successfully",
#             "data": candidate_dict
#         }
        
#     except frappe.DoesNotExistError:
#         frappe.throw(f"Candidate {candidate_id} not found")
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Candidate Details Fetch Failed")
#         frappe.throw(f"Failed to fetch candidate details: {str(e)}")


# @frappe.whitelist(allow_guest=True)
# def update_stage_status():
#     """Update stage status for a candidate"""
#     data = frappe.form_dict
#     frappe.log("Updating stage status: {data}".format(data=json.dumps(dict(data), indent=2)))

#     candidate_id = data.get("candidate_id")
#     stage_id = data.get("stage_id")
#     status = data.get("status")  # pending, in_progress, completed, rejected
#     notes = data.get("notes", "")

#     if not candidate_id:
#         frappe.throw("Candidate ID is required")
    
#     if not stage_id:
#         frappe.throw("Stage ID is required")
    
#     if not status:
#         frappe.throw("Status is required")

#     try:
#         # Validate stage_id
#         valid_stages = [s['id'] for s in RECRUITMENT_STAGES]
#         if stage_id not in valid_stages:
#             frappe.throw(f"Invalid stage ID. Must be one of: {', '.join(valid_stages)}")
        
#         # Create or update stage tracking record
#         # You might want to create a custom DocType for this called "Candidate Stage Status"
#         # For now, we'll use the custom_recruitment_stage field on Job Applicant
        
#         candidate_doc = frappe.get_doc("Job Applicant", candidate_id)
        
#         # Update the recruitment stage
#         stage_label = next(s['label'] for s in RECRUITMENT_STAGES if s['id'] == stage_id)
#         candidate_doc.custom_recruitment_stage = stage_label
        
#         # Add note about the stage update
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         stage_note = f"\n\n[{timestamp}] Stage Update: {stage_label}\nStatus: {status}\n{notes}"
        
#         if candidate_doc.notes:
#             candidate_doc.notes += stage_note
#         else:
#             candidate_doc.notes = stage_note
        
#         candidate_doc.save(ignore_permissions=True)
#         frappe.db.commit()
        
#         frappe.log(f"Updated stage {stage_id} for candidate {candidate_id}: {status}")
        
#         # Get updated stage statuses
#         updated_statuses = get_candidate_stage_statuses(candidate_id)
        
#         return {
#             "message": f"Stage {stage_label} updated to {status}",
#             "data": {
#                 "candidate_id": candidate_id,
#                 "stage_id": stage_id,
#                 "status": status,
#                 "all_stage_statuses": updated_statuses
#             }
#         }
        
#     except frappe.DoesNotExistError:
#         frappe.throw(f"Candidate {candidate_id} not found")
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Stage Status Update Failed")
#         frappe.throw(f"Failed to update stage status: {str(e)}")


# @frappe.whitelist(allow_guest=True)
# def get_stage_statistics():
#     """Get statistics about candidates in each recruitment stage"""
#     try:
#         all_candidates = frappe.get_all("Job Applicant", fields=["name"])
        
#         stage_stats = {stage['id']: {
#             'pending': 0,
#             'in_progress': 0,
#             'completed': 0,
#             'rejected': 0,
#             'label': stage['label']
#         } for stage in RECRUITMENT_STAGES}
        
#         for candidate in all_candidates:
#             stage_statuses = get_candidate_stage_statuses(candidate.name)
#             for stage_status in stage_statuses:
#                 stage_id = stage_status['stage_id']
#                 status = stage_status['status']
#                 if stage_id in stage_stats:
#                     stage_stats[stage_id][status] += 1
        
#         return {
#             "message": "Stage statistics fetched successfully",
#             "data": stage_stats
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Stage Statistics Fetch Failed")
#         frappe.throw(f"Failed to fetch stage statistics: {str(e)}")


# @frappe.whitelist(allow_guest=True)
# def get_candidates_by_stage(stage_id, status=None):
#     """Get candidates filtered by stage and optionally by status within that stage"""
#     try:
#         if not stage_id:
#             frappe.throw("Stage ID is required")
        
#         # Validate stage_id
#         valid_stages = [s['id'] for s in RECRUITMENT_STAGES]
#         if stage_id not in valid_stages:
#             frappe.throw(f"Invalid stage ID. Must be one of: {', '.join(valid_stages)}")
        
#         all_candidates = frappe.get_all(
#             "Job Applicant",
#             fields=[
#                 "name",
#                 "applicant_name",
#                 "email_id",
#                 "phone_number",
#                 "job_title",
#                 "designation",
#                 "status",
#                 "location",
#                 "creation",
#                 "resume_score"
#             ],
#             order_by="creation desc"
#         )
        
#         filtered_candidates = []
        
#         for candidate in all_candidates:
#             stage_statuses = get_candidate_stage_statuses(candidate.name)
#             stage_status = next((s for s in stage_statuses if s['stage_id'] == stage_id), None)
            
#             if stage_status:
#                 # If status filter is provided, check if it matches
#                 if status is None or stage_status['status'] == status:
#                     candidate['current_stage_status'] = stage_status
#                     filtered_candidates.append(candidate)
        
#         stage_label = next(s['label'] for s in RECRUITMENT_STAGES if s['id'] == stage_id)
        
#         return {
#             "message": f"Candidates in stage '{stage_label}' fetched successfully",
#             "data": filtered_candidates,
#             "total": len(filtered_candidates),
#             "stage": stage_label,
#             "status_filter": status
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Candidates By Stage Fetch Failed")
#         frappe.throw(f"Failed to fetch candidates: {str(e)}")


# @frappe.whitelist(allow_guest=True)
# def advance_candidate_to_next_stage():
#     """Automatically advance candidate to the next stage after completing current stage"""
#     data = frappe.form_dict
#     frappe.log("Advancing candidate to next stage: {data}".format(data=json.dumps(dict(data), indent=2)))

#     candidate_id = data.get("candidate_id")
#     current_stage_id = data.get("current_stage_id")

#     if not candidate_id:
#         frappe.throw("Candidate ID is required")
    
#     if not current_stage_id:
#         frappe.throw("Current stage ID is required")

#     try:
#         # Find current stage index
#         current_stage_index = next((i for i, s in enumerate(RECRUITMENT_STAGES) if s['id'] == current_stage_id), None)
        
#         if current_stage_index is None:
#             frappe.throw("Invalid current stage ID")
        
#         # Check if there's a next stage
#         if current_stage_index >= len(RECRUITMENT_STAGES) - 1:
#             return {
#                 "message": "Candidate is already at the final stage",
#                 "data": {
#                     "candidate_id": candidate_id,
#                     "current_stage": RECRUITMENT_STAGES[current_stage_index]['label']
#                 }
#             }
        
#         # Get next stage
#         next_stage = RECRUITMENT_STAGES[current_stage_index + 1]
        
#         # Update candidate to next stage
#         candidate_doc = frappe.get_doc("Job Applicant", candidate_id)
#         candidate_doc.custom_recruitment_stage = next_stage['label']
        
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         stage_note = f"\n\n[{timestamp}] Advanced to: {next_stage['label']}"
        
#         if candidate_doc.notes:
#             candidate_doc.notes += stage_note
#         else:
#             candidate_doc.notes = stage_note
        
#         candidate_doc.save(ignore_permissions=True)
#         frappe.db.commit()
        
#         frappe.log(f"Advanced candidate {candidate_id} to stage: {next_stage['label']}")
        
#         return {
#             "message": f"Candidate advanced to {next_stage['label']}",
#             "data": {
#                 "candidate_id": candidate_id,
#                 "previous_stage": RECRUITMENT_STAGES[current_stage_index]['label'],
#                 "current_stage": next_stage['label'],
#                 "stage_id": next_stage['id']
#             }
#         }
        
#     except frappe.DoesNotExistError:
#         frappe.throw(f"Candidate {candidate_id} not found")
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Advance Stage Failed")
#         frappe.throw(f"Failed to advance candidate to next stage: {str(e)}")


# @frappe.whitelist(allow_guest=True)
# def get_recruitment_pipeline():
#     """Get overview of the recruitment pipeline with candidate counts at each stage"""
#     try:
#         all_candidates = frappe.get_all(
#             "Job Applicant",
#             fields=["name", "applicant_name", "status"],
#             order_by="creation desc"
#         )
        
#         pipeline = []
        
#         for stage in RECRUITMENT_STAGES:
#             candidates_in_stage = []
            
#             for candidate in all_candidates:
#                 stage_statuses = get_candidate_stage_statuses(candidate.name)
#                 current_stage_status = next((s for s in stage_statuses if s['stage_id'] == stage['id']), None)
                
#                 if current_stage_status:
#                     # Consider a candidate "in" a stage if it's in_progress or the first non-completed stage
#                     if current_stage_status['status'] in ['in_progress', 'pending']:
#                         # Check if all previous stages are completed
#                         all_previous_completed = True
#                         for prev_stage in RECRUITMENT_STAGES[:stage['order']-1]:
#                             prev_status = next((s for s in stage_statuses if s['stage_id'] == prev_stage['id']), None)
#                             if not prev_status or prev_status['status'] != 'completed':
#                                 all_previous_completed = False
#                                 break
                        
#                         if all_previous_completed:
#                             candidates_in_stage.append({
#                                 'id': candidate.name,
#                                 'name': candidate.applicant_name,
#                                 'status': current_stage_status['status']
#                             })
            
#             pipeline.append({
#                 'stage_id': stage['id'],
#                 'stage_label': stage['label'],
#                 'candidate_count': len(candidates_in_stage),
#                 'candidates': candidates_in_stage[:5]  # Return first 5 for preview
#             })
        
#         return {
#             "message": "Recruitment pipeline fetched successfully",
#             "data": pipeline,
#             "total_candidates": len(all_candidates)
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Pipeline Fetch Failed")
#         frappe.throw(f"Failed to fetch recruitment pipeline: {str(e)}")




import frappe
from datetime import datetime
import json

# Define recruitment stages - UPDATED WITH JOINING CONFIRMATION
RECRUITMENT_STAGES = [
    {'id': 'interview', 'label': 'Interview', 'order': 1},
    {'id': 'feedback', 'label': 'Candidate Feedback', 'order': 2},
    {'id': 'document_verification', 'label': 'Document Verification', 'order': 3},
    {'id': 'offer_letter', 'label': 'Offer Letter', 'order': 4},
    {'id': 'joining_confirmation', 'label': 'Joining Confirmation', 'order': 5},
    {'id': 'appointment_letter', 'label': 'Appointment Letter', 'order': 6},
]

@frappe.whitelist(allow_guest=True)
def get_all_candidates():
    """Get list of all job applicants with complete details including stage tracking"""
    try:
        candidates = frappe.get_all(
            "Job Applicant",
            fields=[
                "name",
                "applicant_name",
                "email_id",
                "phone_number",
                "job_title",
                "designation",
                "status",
                "country",
                "location",
                "address",
                "source",
                "notes",
                "resume_link",
                "cover_letter",
                "creation",
                "modified",
                "resume_score",
                "custom_recruitment_stage"
            ],
            order_by="creation desc"
        )
        
        # Enrich with stage statuses
        for candidate in candidates:
            candidate["stage_statuses"] = get_candidate_stage_statuses(candidate.name)
        
        frappe.log(f"Fetched {len(candidates)} candidates with stage tracking")
        
        return {
            "message": "Candidates fetched successfully",
            "data": candidates,
            "total": len(candidates)
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Candidates Fetch Failed")
        frappe.throw(f"Failed to fetch candidates: {str(e)}")


def get_candidate_stage_statuses(candidate_id):
    """Get stage statuses for a candidate - UPDATED WITH JOINING CONFIRMATION"""
    statuses = []
    
    try:
        # Stage 1: Interview
        interviews = frappe.get_all(
            "Interview",
            filters={"job_applicant": candidate_id},
            fields=["status", "scheduled_on", "from_time", "to_time"],
            order_by="scheduled_on desc"
        )
        
        if interviews:
            latest_interview = interviews[0]
            if latest_interview.status in ["Completed", "Cleared"]:
                statuses.append({
                    "stage_id": "interview",
                    "status": "completed",
                    "completed_date": latest_interview.scheduled_on,
                    "notes": f"Interview status: {latest_interview.status}"
                })
            elif latest_interview.status == "Rejected":
                statuses.append({
                    "stage_id": "interview",
                    "status": "rejected",
                    "completed_date": latest_interview.scheduled_on,
                    "notes": "Interview rejected"
                })
            else:
                statuses.append({
                    "stage_id": "interview",
                    "status": "in_progress",
                    "notes": f"Interview scheduled for {latest_interview.scheduled_on}"
                })
        else:
            statuses.append({
                "stage_id": "interview",
                "status": "pending",
                "notes": "No interview scheduled yet"
            })
        
        # Stage 2: Feedback
        feedbacks = frappe.get_all(
            "Interview Feedback",
            filters={"job_applicant": candidate_id},
            fields=["creation", "result"],
            order_by="creation desc"
        )
        
        if feedbacks:
            latest_feedback = feedbacks[0]
            statuses.append({
                "stage_id": "feedback",
                "status": "completed",
                "completed_date": latest_feedback.creation,
                "notes": f"Feedback result: {latest_feedback.get('result', 'Submitted')}"
            })
        else:
            interview_completed = any(s for s in statuses if s["stage_id"] == "interview" and s["status"] == "completed")
            statuses.append({
                "stage_id": "feedback",
                "status": "in_progress" if interview_completed else "pending",
                "notes": "Awaiting feedback" if interview_completed else "Complete interview first"
            })
        
        # Stage 3: Document Verification
        documents = frappe.get_all(
            "Applicant Document",
            filters={"applicant_name": candidate_id},
            fields=["name", "creation", "aadhar_card", "pan", "education", "experience", "bank_details"],
            limit=1
        )
        
        if documents:
            doc = documents[0]
            mandatory_docs = ['aadhar_card', 'pan', 'education', 'experience', 'bank_details']
            uploaded_count = sum(1 for field in mandatory_docs if doc.get(field))
            
            if uploaded_count == len(mandatory_docs):
                statuses.append({
                    "stage_id": "document_verification",
                    "status": "completed",
                    "completed_date": doc.creation,
                    "notes": "All mandatory documents uploaded and verified"
                })
            else:
                statuses.append({
                    "stage_id": "document_verification",
                    "status": "in_progress",
                    "notes": f"{uploaded_count}/{len(mandatory_docs)} mandatory documents uploaded"
                })
        else:
            feedback_completed = any(s for s in statuses if s["stage_id"] == "feedback" and s["status"] == "completed")
            statuses.append({
                "stage_id": "document_verification",
                "status": "in_progress" if feedback_completed else "pending",
                "notes": "No documents uploaded yet" if feedback_completed else "Complete previous stages first"
            })
        
        # Stage 4: Offer Letter
        offers = frappe.get_all(
            "Job Offer",
            filters={"job_applicant": candidate_id},
            fields=["name", "creation", "status", "offer_date"],
            order_by="creation desc",
            limit=1
        )
        
        if offers:
            offer = offers[0]
            statuses.append({
                "stage_id": "offer_letter",
                "status": "completed",
                "completed_date": offer.offer_date or offer.creation,
                "notes": f"Offer status: {offer.status}"
            })
        else:
            doc_completed = any(s for s in statuses if s["stage_id"] == "document_verification" and s["status"] == "completed")
            statuses.append({
                "stage_id": "offer_letter",
                "status": "in_progress" if doc_completed else "pending",
                "notes": "Ready to send offer" if doc_completed else "Complete document verification first"
            })
        
        # NEW: Stage 5: Joining Confirmation
        joining_records = frappe.get_all(
            "Joining Confirmation",
            filters={"candidate_id": candidate_id},
            fields=["name", "join", "not_join", "offer_revoked", "modified"],
            order_by="modified desc",
            limit=1
        )
        
        if joining_records:
            joining = joining_records[0]
            
            if joining.get("join") == 1:
                statuses.append({
                    "stage_id": "joining_confirmation",
                    "status": "join",
                    "completed_date": joining.modified,
                    "notes": "Candidate confirmed joining"
                })
            elif joining.get("not_join") == 1:
                statuses.append({
                    "stage_id": "joining_confirmation",
                    "status": "not_join",
                    "completed_date": joining.modified,
                    "notes": "Candidate declined offer"
                })
            elif joining.get("offer_revoked") == 1:
                statuses.append({
                    "stage_id": "joining_confirmation",
                    "status": "offer_revoked",
                    "completed_date": joining.modified,
                    "notes": "Offer revoked by company"
                })
            else:
                statuses.append({
                    "stage_id": "joining_confirmation",
                    "status": "in_progress",
                    "notes": "Awaiting joining confirmation"
                })
        else:
            offer_completed = any(s for s in statuses if s["stage_id"] == "offer_letter" and s["status"] == "completed")
            statuses.append({
                "stage_id": "joining_confirmation",
                "status": "in_progress" if offer_completed else "pending",
                "notes": "Waiting for joining confirmation" if offer_completed else "Complete offer letter first"
            })
        
        # Stage 6: Appointment Letter (UPDATED - now depends on joining confirmation)
        appointments = frappe.get_all(
            "Appointment Letter",
            filters={"applicant_name": candidate_id},
            fields=["name", "creation", "status", "date_of_joining"],
            limit=1
        )
        
        if appointments:
            appointment = appointments[0]
            statuses.append({
                "stage_id": "appointment_letter",
                "status": "completed",
                "completed_date": appointment.date_of_joining or appointment.creation,
                "notes": f"Joining date: {appointment.date_of_joining}"
            })
        else:
            # Only activate if candidate confirmed joining
            joining_confirmed = any(s for s in statuses if s["stage_id"] == "joining_confirmation" and s["status"] == "join")
            statuses.append({
                "stage_id": "appointment_letter",
                "status": "in_progress" if joining_confirmed else "pending",
                "notes": "Ready to send appointment letter" if joining_confirmed else "Candidate must confirm joining first"
            })
        
    except Exception as e:
        frappe.log_error(f"Error getting stage statuses for {candidate_id}: {str(e)}")
    
    return statuses


@frappe.whitelist(allow_guest=True)
def get_candidate_details(candidate_id):
    """Get detailed information about a specific candidate including stage tracking"""
    try:
        if not candidate_id:
            frappe.throw("Candidate ID is required")
        
        candidate = frappe.get_doc("Job Applicant", candidate_id)
        
        # Get related interviews
        interviews = frappe.get_all(
            "Interview",
            filters={"job_applicant": candidate_id},
            fields=[
                "name",
                "interview_round",
                "scheduled_on",
                "from_time",
                "to_time",
                "status",
                "google_meet",
                "custom_location",
                "notes"
            ],
            order_by="scheduled_on desc"
        )
        
        # Get stage statuses
        stage_statuses = get_candidate_stage_statuses(candidate_id)
        
        candidate_dict = candidate.as_dict()
        candidate_dict["interviews"] = interviews
        candidate_dict["stage_statuses"] = stage_statuses
        
        return {
            "message": "Candidate details fetched successfully",
            "data": candidate_dict
        }
        
    except frappe.DoesNotExistError:
        frappe.throw(f"Candidate {candidate_id} not found")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Candidate Details Fetch Failed")
        frappe.throw(f"Failed to fetch candidate details: {str(e)}")


@frappe.whitelist(allow_guest=True)
def update_stage_status():
    """Update stage status for a candidate"""
    data = frappe.form_dict
    frappe.log("Updating stage status: {data}".format(data=json.dumps(dict(data), indent=2)))

    candidate_id = data.get("candidate_id")
    stage_id = data.get("stage_id")
    status = data.get("status")
    notes = data.get("notes", "")

    if not candidate_id:
        frappe.throw("Candidate ID is required")
    
    if not stage_id:
        frappe.throw("Stage ID is required")
    
    if not status:
        frappe.throw("Status is required")

    try:
        # Validate stage_id
        valid_stages = [s['id'] for s in RECRUITMENT_STAGES]
        if stage_id not in valid_stages:
            frappe.throw(f"Invalid stage ID. Must be one of: {', '.join(valid_stages)}")
        
        candidate_doc = frappe.get_doc("Job Applicant", candidate_id)
        
        # Update the recruitment stage
        stage_label = next(s['label'] for s in RECRUITMENT_STAGES if s['id'] == stage_id)
        candidate_doc.custom_recruitment_stage = stage_label
        
        # Add note about the stage update
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stage_note = f"\n\n[{timestamp}] Stage Update: {stage_label}\nStatus: {status}\n{notes}"
        
        if candidate_doc.notes:
            candidate_doc.notes += stage_note
        else:
            candidate_doc.notes = stage_note
        
        candidate_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.log(f"Updated stage {stage_id} for candidate {candidate_id}: {status}")
        
        # Get updated stage statuses
        updated_statuses = get_candidate_stage_statuses(candidate_id)
        
        return {
            "message": f"Stage {stage_label} updated to {status}",
            "data": {
                "candidate_id": candidate_id,
                "stage_id": stage_id,
                "status": status,
                "all_stage_statuses": updated_statuses
            }
        }
        
    except frappe.DoesNotExistError:
        frappe.throw(f"Candidate {candidate_id} not found")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Stage Status Update Failed")
        frappe.throw(f"Failed to update stage status: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_stage_statistics():
    """Get statistics about candidates in each recruitment stage"""
    try:
        all_candidates = frappe.get_all("Job Applicant", fields=["name"])
        
        stage_stats = {stage['id']: {
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'rejected': 0,
            'join': 0,
            'not_join': 0,
            'offer_revoked': 0,
            'label': stage['label']
        } for stage in RECRUITMENT_STAGES}
        
        for candidate in all_candidates:
            stage_statuses = get_candidate_stage_statuses(candidate.name)
            for stage_status in stage_statuses:
                stage_id = stage_status['stage_id']
                status = stage_status['status']
                if stage_id in stage_stats and status in stage_stats[stage_id]:
                    stage_stats[stage_id][status] += 1
        
        return {
            "message": "Stage statistics fetched successfully",
            "data": stage_stats
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Stage Statistics Fetch Failed")
        frappe.throw(f"Failed to fetch stage statistics: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_candidates_by_stage(stage_id, status=None):
    """Get candidates filtered by stage and optionally by status within that stage"""
    try:
        if not stage_id:
            frappe.throw("Stage ID is required")
        
        # Validate stage_id
        valid_stages = [s['id'] for s in RECRUITMENT_STAGES]
        if stage_id not in valid_stages:
            frappe.throw(f"Invalid stage ID. Must be one of: {', '.join(valid_stages)}")
        
        all_candidates = frappe.get_all(
            "Job Applicant",
            fields=[
                "name",
                "applicant_name",
                "email_id",
                "phone_number",
                "job_title",
                "designation",
                "status",
                "location",
                "creation",
                "resume_score"
            ],
            order_by="creation desc"
        )
        
        filtered_candidates = []
        
        for candidate in all_candidates:
            stage_statuses = get_candidate_stage_statuses(candidate.name)
            stage_status = next((s for s in stage_statuses if s['stage_id'] == stage_id), None)
            
            if stage_status:
                if status is None or stage_status['status'] == status:
                    candidate['current_stage_status'] = stage_status
                    filtered_candidates.append(candidate)
        
        stage_label = next(s['label'] for s in RECRUITMENT_STAGES if s['id'] == stage_id)
        
        return {
            "message": f"Candidates in stage '{stage_label}' fetched successfully",
            "data": filtered_candidates,
            "total": len(filtered_candidates),
            "stage": stage_label,
            "status_filter": status
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Candidates By Stage Fetch Failed")
        frappe.throw(f"Failed to fetch candidates: {str(e)}")


@frappe.whitelist(allow_guest=True)
def advance_candidate_to_next_stage():
    """Automatically advance candidate to the next stage after completing current stage"""
    data = frappe.form_dict
    frappe.log("Advancing candidate to next stage: {data}".format(data=json.dumps(dict(data), indent=2)))

    candidate_id = data.get("candidate_id")
    current_stage_id = data.get("current_stage_id")

    if not candidate_id:
        frappe.throw("Candidate ID is required")
    
    if not current_stage_id:
        frappe.throw("Current stage ID is required")

    try:
        # Find current stage index
        current_stage_index = next((i for i, s in enumerate(RECRUITMENT_STAGES) if s['id'] == current_stage_id), None)
        
        if current_stage_index is None:
            frappe.throw("Invalid current stage ID")
        
        # Check if there's a next stage
        if current_stage_index >= len(RECRUITMENT_STAGES) - 1:
            return {
                "message": "Candidate is already at the final stage",
                "data": {
                    "candidate_id": candidate_id,
                    "current_stage": RECRUITMENT_STAGES[current_stage_index]['label']
                }
            }
        
        # Get next stage
        next_stage = RECRUITMENT_STAGES[current_stage_index + 1]
        
        # Update candidate to next stage
        candidate_doc = frappe.get_doc("Job Applicant", candidate_id)
        candidate_doc.custom_recruitment_stage = next_stage['label']
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stage_note = f"\n\n[{timestamp}] Advanced to: {next_stage['label']}"
        
        if candidate_doc.notes:
            candidate_doc.notes += stage_note
        else:
            candidate_doc.notes = stage_note
        
        candidate_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.log(f"Advanced candidate {candidate_id} to stage: {next_stage['label']}")
        
        return {
            "message": f"Candidate advanced to {next_stage['label']}",
            "data": {
                "candidate_id": candidate_id,
                "previous_stage": RECRUITMENT_STAGES[current_stage_index]['label'],
                "current_stage": next_stage['label'],
                "stage_id": next_stage['id']
            }
        }
        
    except frappe.DoesNotExistError:
        frappe.throw(f"Candidate {candidate_id} not found")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Advance Stage Failed")
        frappe.throw(f"Failed to advance candidate to next stage: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_recruitment_pipeline():
    """Get overview of the recruitment pipeline with candidate counts at each stage"""
    try:
        all_candidates = frappe.get_all(
            "Job Applicant",
            fields=["name", "applicant_name", "status"],
            order_by="creation desc"
        )
        
        pipeline = []
        
        for stage in RECRUITMENT_STAGES:
            candidates_in_stage = []
            
            for candidate in all_candidates:
                stage_statuses = get_candidate_stage_statuses(candidate.name)
                current_stage_status = next((s for s in stage_statuses if s['stage_id'] == stage['id']), None)
                
                if current_stage_status:
                    if current_stage_status['status'] in ['in_progress', 'pending']:
                        all_previous_completed = True
                        for prev_stage in RECRUITMENT_STAGES[:stage['order']-1]:
                            prev_status = next((s for s in stage_statuses if s['stage_id'] == prev_stage['id']), None)
                            if not prev_status or prev_status['status'] != 'completed':
                                all_previous_completed = False
                                break
                        
                        if all_previous_completed:
                            candidates_in_stage.append({
                                'id': candidate.name,
                                'name': candidate.applicant_name,
                                'status': current_stage_status['status']
                            })
            
            pipeline.append({
                'stage_id': stage['id'],
                'stage_label': stage['label'],
                'candidate_count': len(candidates_in_stage),
                'candidates': candidates_in_stage[:5]
            })
        
        return {
            "message": "Recruitment pipeline fetched successfully",
            "data": pipeline,
            "total_candidates": len(all_candidates)
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Pipeline Fetch Failed")
        frappe.throw(f"Failed to fetch recruitment pipeline: {str(e)}")


# NEW: Update joining confirmation function
@frappe.whitelist(allow_guest=True)
def update_joining_confirmation():
    """
    Update joining confirmation status for a candidate
    status_type: 'join', 'not_join', or 'offer_revoked'
    """
  data = frappe.request.get_json()
    
    candidate_id = data.get('candidate_id')
    status_type = data.get('status_type')
    
    frappe.logger().info(f"=== UPDATE JOINING CONFIRMATION ===")
    frappe.logger().info(f"Candidate ID: {candidate_id}")
    frappe.logger().info(f"Status Type: {status_type}")
    
    try:
        if not candidate_id:
            return {
                "success": False,
                "message": "Candidate ID is required"
            }
        
        if status_type not in ['join', 'not_join', 'offer_revoked']:
            return {
                "success": False,
                "message": "Invalid status type. Must be: join, not_join, or offer_revoked"
            }
        
        # Check if a Joining Confirmation record already exists
        existing_records = frappe.get_all(
            "Joining Confirmation",
            filters={"candidate_id": candidate_id},
            fields=["name"]
        )
        
        if existing_records:
            # Update existing record
            frappe.logger().info(f"Updating existing record: {existing_records[0].name}")
            doc = frappe.get_doc("Joining Confirmation", existing_records[0].name)
        else:
            # Create new record
            frappe.logger().info("Creating new record")
            doc = frappe.new_doc("Joining Confirmation")
            doc.candidate_id = candidate_id
        
        # Reset all statuses
        doc.join = 0
        doc.not_join = 0
        doc.offer_revoked = 0
        
        # Set the selected status
        doc.set(status_type, 1)
        frappe.logger().info(f"Setting {status_type} = 1")
        
        # Save the document
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.logger().info("=== SUCCESS ===")
        
        return {
            "success": True,
            "message": f"Joining confirmation updated: {status_type.replace('_', ' ').title()}",
            "data": {
                "candidate_id": candidate_id,
                "status": status_type
            }
        }
        
    except Exception as e:
        frappe.logger().error(f"=== ERROR ===")
        frappe.logger().error(f"Error: {str(e)}")
        frappe.logger().error(f"Traceback: {frappe.get_traceback()}")
        
        frappe.log_error(f"Error updating joining confirmation: {str(e)}")
        frappe.db.rollback()
        
        return {
            "success": False,
            "message": f"Failed to update joining confirmation: {str(e)}"
        }

