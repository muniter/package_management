// Form script for Transportation Trip
frappe.ui.form.on('Transportation Trip', {
    onload(frm) {
        // Create the window_to_update array for updating changes in pacakgers to_collect and destination
        window.packages_to_update = new Set();
        // Get the default origin and set it in origin if it's empty
        frappe.db.get_single_value('Package Management Settings', 'default_origin').then((r) => {
            if (!frm.doc.origin) {
                frm.set_value('origin', r);
            }
        });

        // Trigger state for the buttons to populate.
        frm.trigger('state');
        // Set query to select the packages.
        frm.set_query("package", "packages", () => {
            let curr_packages = frm.doc.packages.map(x => x.package);
            return {
                filters: {
                    state: ['in', ['origin', 'transfer', 'returned']],
                    name: ['not in', curr_packages]
                }
            }
        });

        // Further setup
        frm.get_field("stops").grid.set_multiple_add("stop");
        frm.get_field("packages").grid.set_multiple_add("package");
    },
    before_save(frm) {
        if (frm.doc.state === 'completed') {
            let missing_end_events = new Array()
            frm.doc.packages.forEach((x) => {
                if (!x.end_event) {
                    missing_end_events.push(`${x.idx} - ${x.package}`);
                }
            });
            if (missing_end_events.length) {
                frappe.throw(__("All packages should have End Events before saving, packages missing {0}", [missing_end_events.join("<br>")]))
            };
        }
        // Update the changes to destination an collect in the parent doctype
        // packages is a set of Transportation Trip Packages names,
        // we need it as an Array to stringify it. And also pass the object
        // to the server side method instead of just the name.
        let packages = Array.from(window.packages_to_update)
        packages = packages.map(p => frappe.get_doc('Transportation Trip Package', p))
        console.log(packages);
        if(packages.length) {
            frappe.call({
                method: "package_management.package_management.doctype.transportation_trip.transportation_trip.update_package_fields",
                args: {
                    "packages": packages
                },
                callback: (r) => {
                    console.log(r);
                }
            })
        }
    },
    after_save(frm) {
        // Buttons were disappearing after save, this way I trigger
        // and they show up.
        frm.trigger('state');
    },
    state(frm) {
        // Remove all buttons fierts
        frm.clear_custom_buttons();
        let state = frm.doc.state;
        let packages = frm.doc.packages;
        if (['planned', 'loaded'].includes(state)) {
            frm.add_custom_button(__("Autofill Stops"), () => {
                frm.call('autofill_stops')
                    .then(r => {
                        if (r.message) {
                            frm.refresh();
                            console.log("The response is: ", r);
                        };
                    })
            });
            frm.add_custom_button(__("Fill from Stops"), () => {
                let stops = frm.doc.stops.map(x => x.stop);
                console.log(stops);
                let curr_packages = packages.map(x => x.package);
                frappe.db.get_list('Package', {
                    fields: ['name'],
                    page_length: 100,
                    filters: {
                        state: ['in', ['origin', 'transfer', 'returned']],
                        name: ['not in', curr_packages],
                        destination: ['in', stops]
                    }
                }).then((r) => {
                    console.log(r);
                    r.forEach((p) => {
                        frm.add_child('packages', {'package': p.name});
                    })
                    frm.refresh_field('packages');
                });
            });
        } else if (state === 'completed') {
            frm.add_custom_button(__("Create Events"), () => {
                createEvents(frm);
            });
        };
        // If state is not completed and there are package events.
        if (state !== 'completed' && packages.filter(x => x.end_event).length) {
            frappe.confirm(__("Packages end events should only be set if the Transportation Trip is completed, press yes to delete the package events, or no to set the current trip as completed"),
                () => {
                    // If yes, delete all end_events and destinations
                    frm.doc.packages.forEach(x => {
                        x.end_event = '';
                        x.end_destination = '';
                        x.return_code = '';
                    })
                    frm.refresh()
                    // Have to trigger again since a bug hides the buttons.
                    frm.trigger('state')
                },
                () => {
                    // If No, set back the state to initial state, completed.
                    frm.doc.state = 'completed';
                    frm.refresh()
                });
        }
    }
});

// Form script for Transportation Trip Package child table.
frappe.ui.form.on('Transportation Trip Package', {
    to_collect(frm, cdt, cdn) {
        // Added to the window object to be processed in the before_save hook
        // In which changes to this object will be propagated to the parent
        if (cdn !== undefined) {
            window.packages_to_update.add(cdn);
        }
    },
    destination(frm, cdt, cdn) {
        // Added to the window object to be processed in the before_save hook
        // In which changes to this object will be propagated to the parent
        if (cdn !== undefined) {
            window.packages_to_update.add(cdn);
        }
    },
    package(frm, cdt, cdn) {
        frm.refresh();
        let packages = frm.doc.packages;
        let index = packages.findIndex(p => p.name === cdn);
        let row = frappe.get_doc(cdt, cdn)
        // Throw an error when adding duplicate packages.
        packages.forEach((p) => {
            if (p.name !== row.name && p.package === row.package) {
                packages.pop(row.idx);
                frm.refresh();
                frappe.show_alert(__('Package {0} is a duplicate, removing', [row.package]));
            }
        })
        // Manually fetch fields, since Add Multiple doesn't do it.
        if (!row.destination || !row.to_collect) {
            frappe.model.with_doc("Package", row.package, () => {
                let doc = frappe.model.get_doc('Package', row.package);
                row.destination = doc.destination
                row.to_collect = doc.to_collect
                console.log(doc);
                console.log(cur_frm);
                frm.refresh_field('packages');
            });
        }
    }
});

// Function that handles the dialog for setting the end events.
function createEvents(frm) {
    // Default origin, is used to set the end_destination on returns, etc.
    let dialog = new frappe.ui.Dialog({
        title: 'Quick Package Entry',
        fields: [
            {
                label: __('Barcode'),
                fieldname: 'barcode',
                fieldtype: 'Data',
            },
            {
                label: __('Event'),
                fieldname: 'event',
                fieldtype: 'Select',
                options: frappe.meta.get_docfield('Transportation Trip Package', 'end_event').options,
                reqd: 1
            },
            {
                // TODO: Hidden depending on event type
                label: __('End Destination'),
                fieldname: 'end_destination',
                fieldtype: 'Link',
                options: 'Package Location',
                default: frm.doc.origin,
                reqd: 0
            },
            {
                label: __('Packages'),
                fieldname: 'packages',
                fieldtype: 'Table',
                cannot_add_rows: false,
                reqd: 1,
                in_place_edit: true,
                data: get_data(),
                fields: [
                {
                    label: __('Package'),
                    fieldtype:'Link',
                    fieldname:'package',
                    options: 'Package',
                    in_list_view: 1,
                    read_only: 0,
                    reqd: 1,
                    get_query: () => {
                        let trip_packages = frm.doc.packages.map(x => x.package)
                        return {filters: {name:['in', trip_packages] }};
                    }
                },
                {
                    label: __('RC'),
                    fieldtype:'Select',
                    fieldname:'return_code',
                    options: frm.fields_dict.packages.grid.fields_map.return_code.options,
                    in_list_view: 1,
                    hidden: 1,
                    read_only: 0,
                    reqd: 1,
                }
                ]
            }
        ],
        primary_action_label: __('Set Event'),
        primary_action(values) {
            console.log(values);
            dialog.hide();

            frm.doc.packages.map((p) => {
                let dialog_package = values.packages.find(x => x.package === p.package)
                if (dialog_package) {
                    p.end_event = values.event;
                    p.return_code = dialog_package.return_code;
                    p.end_destination = values.end_destination;
                }
            })
            frm.refresh_field('packages');
            frm.dirty();
        }

    });

    // OBJECT EVENTS //

    // Set the packages field as the selected packages in the form packages table
    // if anything is selected, and clears the selection.
    function get_data() {
        let data = [];
        let grid = frm.fields_dict.packages.grid;
        let selected = frm.get_selected().packages;

        let packages = frm.doc.packages;
        if (selected) {
            selected.forEach((x) => {
                data.push({package: packages.find(e => e.name === x).package})
            });
        };
        // Clear the selection
        grid.grid_rows.map(r => {r.doc.__checked = 0;});
        return data
    };

    // Event to track value of event field, to show or hide destination field.
    // or return code field if returned event is selected
    let end_destination = dialog.fields_dict.end_destination;
    let packages = dialog.fields_dict.packages;
    dialog.$wrapper.on('change', 'select[data-fieldname="event"]', (e) => {
        let target = e.currentTarget;
        if (target.value === 'delivered') {
            end_destination.$wrapper.hide();
            end_destination.set_value('');
        } else if (target.value === 'returned') {
            // Create a new table field with RC, hide the old one
            let wrapper = packages.wrapper;
            packages.grid.fields_map.return_code.hidden = 0;
            packages.make();
            wrapper.remove();
            dialog.refresh();
        } else {
            // end_destination.set_value('');
            if (packages.grid.fields_map.return_code.hidden === 0) {
                // Create a new table field without RC, hide the old one
                let wrapper = packages.wrapper;
                packages.grid.fields_map.return_code.hidden = 1;
                packages.make();
                wrapper.hidden = true;
                dialog.refresh();
            }
            end_destination.$wrapper.show();
            end_destination.set_value(frm.doc.origin);
        };
    });

    // Event for enter event in the input fields, meaning when the barcode scanner is used.
    // Adds it to the packages if it maches any package guide on the list.
    dialog.$wrapper.on('keydown', 'input[data-fieldname="barcode"]', (e) => {
        // Return/Enter key is pressed.
        if(e.which === 13) {
            // Stop Propagation and default event, otherwise the dialog primary action is executed.
            e.preventDefault();
            e.stopPropagation();
            // The guide number is after the first hypen, so slice it on the index of -
            let inputfield = e.currentTarget;
            let guide = processGuide(inputfield.value)
            e.currentTarget.value = '';
            let grid = dialog.fields_dict.packages.grid;
            let df = dialog.fields_dict.packages.df;
            let pack = frm.doc.packages.filter((x) => x.package.slice(x.package.indexOf('-')+1) === guide);
            // There should only be one match.
            if (pack.length) {
                // Check is not already scanned, e.g part of df.data.array
                if (!df.data.filter((x) => x.package === pack[0].package).length) {
                    df.data.push({
                        idx: df.data.length + 1,
                        package: pack[0].package
                    })
                } else {
                    frappe.show_alert(__("Package with guide {0} is already in the list", [guide]))
                }
                // Clear checked items
                grid.refresh();
                guide = ''
            } else {
                frappe.show_alert(__("No package found with guide {0} in this trip", [guide]))
            }
            guide = ''
        }
    });
    // Open the dialog when the function is called.
    dialog.show();
};

function processGuide(guide) {
    let re = /^(\d{4}20\d{2})(\d{5,20})$/;
    return guide.replace(re, '$2')
}
