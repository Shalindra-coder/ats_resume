

frappe.ui.form.on('Job Opening', {
    refresh(frm) {
        // Fetch the recruiter_type field from the User doctype for the current logged-in user
        frappe.db.get_value('User', frappe.session.user, 'recruiter_type', (r) => {
            // Store the recruiter_type in the frm object to use it in the button function
            frm.recruiter_type = r.recruiter_type;
            update_upload_cv_button(frm);
        });
    },
    custom_vertical(frm) {
        update_upload_cv_button(frm);
    }
});

function update_upload_cv_button(frm) {
    // Clear any existing custom buttons to avoid duplication
    frm.clear_custom_buttons();

    // Set default values (These will be used for "Franchise" users regardless of vertical)
    let button_label = "Parse CV";
    let action_type = "Parse";

    if (frm.recruiter_type !== "Franchise") {
        if (frm.doc.custom_vertical === "Permanent Staffing") {
            button_label = "Parse CV and Score";
            action_type = "Score";
        }
    }

    // Add the dynamic custom button
    frm.add_custom_button(__(button_label), () => {
        new frappe.ui.FileUploader({
            allow_multiple: true,
            restrictions: {
                allowed_file_types: ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png']
            },
            on_success(file) {
                if (action_type === "Parse") {
                    // Scenario: Direct parsing (No scoring/justification)
                    frappe.call({
                        method: "resume.resume.upload.parse_cv_and_create_applicant_direct",
                        args: {
                            file_url: file.file_url,
                            job_id: frm.doc.name,
                            designation: frm.doc.designation
                        },
                        freeze: true,
                        freeze_message: __("Parsing CV..."),
                        callback(r) {
                            if (!r.exc && r.message) {
                                frappe.show_alert({
                                    message: __("Applicant created: {0}").format(r.message.applicant_name),
                                    indicator: 'green'
                                });
                                frm.reload_doc();
                            }
                        }
                    });
                } else {
                    // Scenario: Create PDF Upload record first, then trigger scoring process
                    frappe.call({
                        method: "resume.resume.upload.save_cv_to_pdf_upload",
                        args: {
                            file_url: file.file_url,
                            job_id: frm.doc.name,
                            designation: frm.doc.designation,
                            action: action_type
                        },
                        freeze: true,
                        freeze_message: __("Saving CV..."),
                        callback(r) {
                            if (!r.message) return;
                            frappe.show_alert({
                                message: __("CV uploaded successfully"),
                                indicator: 'green'
                            });
                            // Trigger the background processing for parsing and scoring
                            frappe.call({
                                method: "resume.resume.doctype.pdf_upload.pdf_upload.process_pdfs",
                                args: { docname: r.message },
                                freeze: true,
                                freeze_message: __("Parsing & Scoring CV..."),
                                callback() {
                                    frappe.show_alert({
                                        message: __("CV processing started in background"),
                                        indicator: 'blue'
                                    });
                                }
                            });
                        }
                    });
                }
            }
        });
    });
}