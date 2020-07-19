// C
// opyright (c) 2020, Lintec Tecnología and contributors
// For license information, please see license.txt

// Dialog to fill Packages it calls a backend method to get the available packages
// Which returns only ones that are valid for entry, then the user selects the 
// packages they want on the trip, and another backend method is called to set
// the packages in the Trasnportation Trip
// const dialog = new frappe.ui.Dialog({
//     title: __("Quick Package Entry"),
//     fields: [
//         {
//             fieldtype:'Section Break', label: __('Packages')
//         }, {
//             fieldname: "available_packages",
//             fieldtype: "Table",
//             cannot_add_rows: false,
//             in_place_edit: true,
//             data: this.get_data,
//             get_data() {
//                 // It only resolves when I press something, but It works
//                 // This is crucial (me), for async, I don't really understand it
//                 let me = this;
//                 frappe.call({
//                     method: "package_management.package_management.doctype.package.package.get_available_packages_for_trip",
//                     callback: function (r) {
//                         me.message = r.message;
//                     }
//                 })
//                 return me.message
//             },
//             fields: [{
//                 fieldtype:'Link',
//                 fieldname:'name',
//                 options: 'Package',
//                 in_list_view: 1,
//                 read_only: 1,
//                 reqd: 1,
//                 columns: 2,
//                 label: __('Package')
//             }, {
//                 fieldtype:'Data',
//                 fieldname:"destination",
//                 // fetch_from: "package.destination",
//                 read_only: 1,
//                 columns: 3,
//                 in_list_view: 1,
//                 label: __('Destination'),
//             }]
//         }
//     ],
//     primary_action: function(values) {
//         let packages = values.available_packages
//         packages = packages.filter((x) => x.__checked);
//         console.log(packages)
//         let me = this;
//         frappe.call({
//             method: "package_management.package_management.doctype.transportation_trip.transportation_trip.fill_packages",
//             args: {
//                 "packages": packages,
//             },
//             callback: function (r) {
//                 console.log(dialog);
//                 me.message = r.message;
//             }
//         })
//     },
//     primary_action_label: __('Update')
// });

// frappe.ui.form.on('Transportation Trip', {
//     // on refresh event
//     state(frm) {
//         frm.refresh()
//     },
//     onload_post_render(frm) {
//         frm.get_field("stops").grid.set_multiple_add("stop");
//         frm.get_field("packages").grid.set_multiple_add("package");
//     },
//     refresh(frm) {
//         // Custom button to autofill the stops
//         console.log("Form state:", frm.doc.state);
//         if (['planned', 'loaded'].includes(frm.doc.state)) {
//             frm.add_custom_button(__("Autofill Stops"), () => {
//                 frm.call('autofill_stops')
//                     .then(r => {
//                         if (r.message) {
//                             // Hack, because for some reason the save button
//                             // does not show up after the change
//                             frm.save();
//                             console.log("The response is: ", r);
//                         };
//                     })
//             });
//             frm.add_custom_button(__("Quick Package entry"), () => {
//                 dialog.show();
//             });
//         }

//     },
// })
// // MultiSelectDialog with custom query method
// // let query_args = {
// //     query:"package_management.package_management.doctype.package.package.get_packages_for_trip",
// //     filters: { docstatus: ["!=", 2]}
// // }

// // var multi = new frappe.ui.form.MultiSelectDialog({
// //     doctype: "Package",
// //     target: frappe.ui.form.on('Package', {}),
// //     setters: {
// //         "state": "packages.state",
// //     },
// //     date_field: "received_date",
// //     get_query() {
// //         return query_args;
// //     },
// //     action(selections) {
// //         console.log(selections);
// //     }
// // })
