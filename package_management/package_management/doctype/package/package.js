// Copyright (c) 2020, Lintec Tecnología and contributors
// For license information, please see license.txt

// frappe.ui.form.on('Package', {
//     onload_post_render: function(frm) {
//         let datetime = frappe.datetime.now_datetime();
//         if (!frm.doc.received_date) {
//             console.log("Setting date to now")
//             frm.set_value('received_date', datetime);
//         }
//         if (!frm.doc.origin) {
//             console.log("Setting default origin")
//             frappe.db.get_single_value("Package Management Settings",
//                 "default_origin").then((value) => value ? frm.set_value('origin', value) : '');
//         }

//     },
// });
