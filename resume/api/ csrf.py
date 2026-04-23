import frappe

@frappe.whitelist()
def get_csrf_token():
    return frappe.session.csrf_token

    