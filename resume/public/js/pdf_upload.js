



frappe.ui.form.on('PDF Upload', {
    refresh(frm) {
        frm.add_custom_button('Upload Resumes', () => {
            // Check karein ki mandatory fields bhari hain ya nahi
            if (!frm.doc.job_title) {
                frappe.msgprint(__("Please select a Job Title first."));
                return;
            }

            new frappe.ui.FileUploader({
                allow_multiple: true,
                restrictions: {
                    allowed_file_types: ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png']
                },
                on_success(file) {
                    // Child table mein file add karein
                    let row = frm.add_child("files");
                    row.file_upload = file.file_url;
                    frm.refresh_field("files");
                },
                on_complete() {
                    frappe.show_alert({message: __("All files uploaded. Saving..."), indicator: 'blue'});
                    
                    // Forcefully form ko dirty mark karein taki save trigger ho
                    frm.dirty(); 

                    frm.save().then(() => {
                        // Agar save successful hua, tabhi Python call karein
                        frappe.call({
                            method: "resume.resume.doctype.pdf_upload.pdf_upload.process_pdfs",
                            args: {
                                docname: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __("AI is analyzing resumes..."),
                            callback: (r) => {
                                if (!r.exc) {
                                    frappe.msgprint({
                                        title: __('Success'),
                                        indicator: 'green',
                                        message: __('Resumes are being processed. Check Job Applicants after 1-2 minutes.')
                                    });
                                    frm.reload_doc();
                                }
                            },
                            error: (err) => {
                                frappe.msgprint(__("An error occurred during processing."));
                            }
                        });
                    }).catch((e) => {
                        frappe.msgprint(__("Save failed. Please check if all mandatory fields are filled."));
                        console.error("Save Error: ", e);
                    });
                }
            });
        });
    }
});