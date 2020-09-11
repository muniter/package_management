// Copyright (c) 2020, Lintec Tecnología and contributors
// For license information, please see license.txt

frappe.ui.form.on('Package', {
    onload_post_render: function(frm) {
        let datetime = frappe.datetime.now_datetime();
        if (!frm.doc.received_date) {
            console.log("Setting date to now")
            frm.set_value('received_date', datetime);
        }
        if (!frm.doc.origin) {
            console.log("Setting default origin")
            frappe.db.get_single_value("Package Management Settings",
                "default_origin").then((value) => value ? frm.set_value('origin', value) : '');
        }
        frm.trigger('completed');
    },
    // after_save: function(frm) {
    //     frm.trigger('completed');
    // },
    completed: function(frm) {
        let completed = frm.doc.completed

        // Enable fetch button depending on completed
        if (frm.doc.fetchable && !completed) {
            frm.add_custom_button(__("Fetch Data"), () => {
                frm.call('fetch_package')
                    .then((r) => {
                        if (r.message) {
                            frappe.show_alert(__("Succesful Update, Reloading document"))
                            frm.reload_doc();
                        } else {
                            frappe.show_alert(__("No data updated"))
                        }
                    })
            })
        } else {
            frm.remove_custom_button(__("Fetch Data"))
        }

        // Things are read only if completed is checked.
        // and toggled back if not checked.
        let fields = frm.fields.filter((f) => {
            return f.df.fieldname !== 'completed';
        })
        fields.forEach((f) => {
            f.df.read_only = completed;
        })
        frm.refresh_fields();
    },
});
