"""Create custom fields for Job Applicant doctype."""
import frappe

def create_custom_fields():
    """Create custom fields for Job Applicant."""
    custom_fields = [
        {
            "dt": "Job Applicant",
            "fieldname": "justification_by_ai",
            "fieldtype": "Small Text",
            "label": "Justification By AI",
            "insert_after": None,
        },
        {
            "dt": "Job Applicant",
            "fieldname": "fit_level",
            "fieldtype": "Select",
            "label": "Fit Level",
            "options": "Strong Fit\nModerate Fit\nWeak Fit",
            "insert_after": "justification_by_ai",
        },
        {
            "dt": "Job Applicant",
            "fieldname": "score",
            "fieldtype": "Int",
            "label": "Score",
            "insert_after": "fit_level",
        }
    ]
    
    for field_data in custom_fields:
        # Check if field already exists
        field_name = f"{field_data['dt']}-{field_data['fieldname']}"
        if not frappe.db.exists("Custom Field", field_name):
            custom_field = frappe.get_doc({
                "doctype": "Custom Field",
                **field_data
            })
            custom_field.insert(ignore_permissions=True)
            frappe.logger().info(f"Created custom field: {field_data['fieldname']}")
        else:
            frappe.logger().info(f"Custom field already exists: {field_data['fieldname']}")
    
    frappe.db.commit()


