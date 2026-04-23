frappe.ui.form.on('Job Opening', {
    refresh(frm) {
        update_upload_cv_button(frm);
    },
    custom_vertical(frm) {
        update_upload_cv_button(frm);
    }
});

function update_upload_cv_button(frm) {
    frm.clear_custom_buttons();

    let button_label = "Parse CV";
    let action_type = "Parse";

    if (frm.doc.custom_vertical === "Permanent Staffing") {
        button_label = "Parse CV and Score";
        action_type = "Score";
    }

    frm.add_custom_button(__(button_label), () => {
        new frappe.ui.FileUploader({
            allow_multiple: true,
            restrictions: {
                allowed_file_types: ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png']
            },
            on_success(file) {
                if (action_type === "Parse") {
                    // Direct: parse CV and create Job Applicant (no PDF Upload, no score/fit/justification)
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
                    // Score: create PDF Upload, then process with scoring
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
