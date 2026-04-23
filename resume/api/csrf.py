
import frappe
@frappe.whitelist()
def get_csrf_token():
    return frappe.sessions.get_csrf_token()