import frappe
from datetime import datetime, timezone
import json

@frappe.whitelist(allow_guest=True)
def create_interview_event():
    """Create a new interview event"""
    data = frappe.form_dict
    frappe.log("Received interview event data: {data}".format(data=json.dumps(dict(data), indent=2)))

    # Define required fields
    required_fields = ["interview_round", "job_applicant", "scheduled_on", "from_time", "to_time", "status"]
    for field in required_fields:
        if not data.get(field):
            frappe.throw(f"{field} is required")

    # Validate status
    status = data.get("status")
    frappe.log(f"status received: {status}")
    valid_statuses = ["Pending", "Scheduled", "Completed", "Cancelled", "Cleared", "Under Review", "Rejected"]
    if not status or status not in valid_statuses:
        frappe.throw(f"Invalid or missing status. Must be one of {', '.join(valid_statuses)}")

    # Validate time range
    from_time = data.get("from_time")
    to_time = data.get("to_time")
    
    if from_time and to_time:
        try:
            from_dt = datetime.strptime(from_time, "%H:%M")
            to_dt = datetime.strptime(to_time, "%H:%M")
            
            if from_dt >= to_dt:
                frappe.throw("From Time must be earlier than To Time")
        except ValueError:
            frappe.throw("Invalid time format. Please use HH:MM format")

    # Get location (optional field)
    location = data.get("location", "").strip() or None

    try:
        # Create the Interview document
        interview_doc = frappe.get_doc({
            "doctype": "Interview",
            "interview_round": data.interview_round,
            "job_applicant": data.job_applicant,
            "resume_link": data.get("resume_link"),
            "google_meet": data.get("meeting_link"),
            "custom_location": location,
            "status": status,
            "scheduled_on": data.scheduled_on,
            "from_time": from_time,
            "to_time": to_time,
            "notes": data.get("notes"),
        })
        
        # Add interviewers if provided
        if data.get("interviewers"):
            interviewers = json.loads(data.interviewers) if isinstance(data.interviewers, str) else data.interviewers
            for interviewer in interviewers:
                interview_doc.append("interview_details", {
                    "interviewer": interviewer
                })
        
        interview_doc.insert(ignore_permissions=True, ignore_links=True)
        frappe.db.commit()
        
        frappe.log(f"Created interview: {interview_doc.name}, status: {interview_doc.status}")
        return {
            "message": f"Interview {interview_doc.name} created successfully.",
            "doc": interview_doc.as_dict()
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interview Creation Failed")
        frappe.throw(f"Failed to create interview due to a server error. Please contact support.")


@frappe.whitelist(allow_guest=True)
def get_interview_list():
    """Get list of all interviews"""
    try:
        interviews = frappe.get_all(
            "Interview",
            fields=[
                "name",
                "interview_round",
                "job_applicant",
                "resume_link",
                "google_meet",
                "custom_location",
                "status",
                "scheduled_on",
                "from_time",
                "to_time",
                "notes",
                "creation",
                "modified"
            ],
            order_by="scheduled_on desc"
        )
        
        # Get interviewers for each interview
        for interview in interviews:
            interviewers = frappe.get_all(
                "Interview Detail",
                filters={"parent": interview.name},
                fields=["interviewer"]
            )
            interview["interviewers"] = [i.interviewer for i in interviewers]
            
            # Map google_meet to meeting_link for frontend
            if "google_meet" in interview:
                interview["meeting_link"] = interview.get("google_meet")
            if "custom_location" in interview:
                interview["location"] = interview.get("custom_location")
        
        return {
            "message": "Interviews fetched successfully",
            "data": interviews
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interview List Fetch Failed")
        frappe.throw("Failed to fetch interviews")


@frappe.whitelist(allow_guest=True)
def get_interview_details(interview_name):
    """Get details of a specific interview"""
    try:
        if not interview_name:
            frappe.throw("Interview name is required")
        
        interview = frappe.get_doc("Interview", interview_name)
        
        # Get interviewers
        interviewers = frappe.get_all(
            "Interview Detail",
            filters={"parent": interview_name},
            fields=["interviewer", "name"]
        )
        
        interview_dict = interview.as_dict()
        interview_dict["interviewers"] = [i.interviewer for i in interviewers]
        
        # Map google_meet to meeting_link for frontend
        if hasattr(interview, 'google_meet'):
            interview_dict["meeting_link"] = interview.google_meet
        if hasattr(interview, 'custom_location'):
            interview_dict["location"] = interview.custom_location
        
        return {
            "message": "Interview details fetched successfully",
            "data": interview_dict
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interview Details Fetch Failed")
        frappe.throw(f"Failed to fetch interview details: {str(e)}")


@frappe.whitelist(allow_guest=True)
def update_interview_event():
    """Update an existing interview"""
    data = frappe.form_dict
    frappe.log("Updating interview event: {data}".format(data=json.dumps(dict(data), indent=2)))

    interview_name = data.get("name")
    if not interview_name:
        frappe.throw("Interview name is required for update")

    try:
        interview_doc = frappe.get_doc("Interview", interview_name)
        
        # Update fields if provided
        if data.get("interview_round"):
            interview_doc.interview_round = data.interview_round
        if data.get("job_applicant"):
            interview_doc.job_applicant = data.job_applicant
        if data.get("resume_link"):
            interview_doc.resume_link = data.resume_link
        if data.get("meeting_link"):
            interview_doc.google_meet = data.meeting_link
        if data.get("location"):
            interview_doc.custom_location = data.location
        if data.get("status"):
            interview_doc.status = data.status
        if data.get("scheduled_on"):
            interview_doc.scheduled_on = data.scheduled_on
        if data.get("from_time"):
            interview_doc.from_time = data.from_time
        if data.get("to_time"):
            interview_doc.to_time = data.to_time
        if data.get("notes"):
            interview_doc.notes = data.notes
        
        # Update interviewers if provided
        if data.get("interviewers"):
            interview_doc.interview_details = []
            interviewers = json.loads(data.interviewers) if isinstance(data.interviewers, str) else data.interviewers
            for interviewer in interviewers:
                interview_doc.append("interview_details", {
                    "interviewer": interviewer
                })
        
        interview_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.log(f"Updated interview: {interview_doc.name}")
        return {
            "message": f"Interview {interview_doc.name} updated successfully.",
            "doc": interview_doc.as_dict()
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interview Update Failed")
        frappe.throw(f"Failed to update interview: {str(e)}")


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
def get_interviewers():
    """Get list of available interviewers (users with interviewer role)"""
    try:
        interviewers = frappe.get_all(
            "User",
            filters={
                "enabled": 1,
                "name": ["!=", "Administrator"]
            },
            fields=["name", "full_name", "email"],
            order_by="full_name"
        )
        
        return {
            "message": "Interviewers fetched successfully",
            "data": interviewers
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interviewers Fetch Failed")
        frappe.throw("Failed to fetch interviewers")


@frappe.whitelist(allow_guest=True)
def delete_interview(interview_name):
    """Delete an interview"""
    try:
        if not interview_name:
            frappe.throw("Interview name is required")
        
        frappe.delete_doc("Interview", interview_name, ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "message": f"Interview {interview_name} deleted successfully"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interview Deletion Failed")
        frappe.throw(f"Failed to delete interview: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_interview_rounds():
    """Get list of interview rounds"""
    try:
        rounds = frappe.get_all(
            "Interview Round",
            fields=["name", "round_name"],
            order_by="name"
        )
        
        return {
            "message": "Interview rounds fetched successfully",
            "data": rounds
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interview Rounds Fetch Failed")
        frappe.throw("Failed to fetch interview rounds")

        