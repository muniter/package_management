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
        frm.trigger('buttons');
        frm.trigger('completed');
    },
    after_save: function(frm) {
        frm.trigger('buttons');
    },
    completed: function(frm) {
        // Things are read only if completed is checked.
        let completed = frm.doc.completed
        console.log("Setting read_only as", completed);
        let fields = frm.fields.filter((f) => {
            return f.df.fieldname !== 'completed';
        })
        fields.forEach((f) => {
            f.df.read_only = completed;
        })
        frm.refresh();
    },
    buttons: function (frm) {
        if (frm.doc.fetchable && !frm.doc.completed) {
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
        }
    }
});
