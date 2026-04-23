frappe.ui.form.on('PDF Upload', {
    refresh: function(frm) {
        frm.add_custom_button('Process All PDFs', function() {
            frappe.call({
                method: 'resume.resume.doctype.pdf_upload.pdf_upload.process_pdfs',
                args: { docname: frm.doc.name },
                callback: function(response) {
                    frappe.msgprint('All PDF Files Processed Successfully');
                    frm.reload_doc();
                }
            });
        });
    }
});
