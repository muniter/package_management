function quickPackageCreation () {
    let dialog = new frappe.ui.Dialog({
        title: 'Quick Package Entry',
        fields: [
            {
                label: __('Customer'),
                fieldname: 'customer',
                fieldtype: 'Link',
                options: 'Customer',
                reqd: 1
            },
            {
                label: __('Barcode'),
                fieldname: 'barcode',
                fieldtype: 'Data',
            },
            {
                label: __('Packages'),
                fieldname: 'packages',
                fieldtype: 'Table',
                cannot_add_rows: false,
                reqd: 1,
                in_place_edit: true,
                data: [],
                fields: [{
                    label: __('Guide Number'),
                    fieldtype:'Data',
                    fieldname:'guide',
                    in_list_view: 1,
                    read_only: 0,
                    reqd: 1,
                    columns: 3
                },
                    {
                        label: __('Type'),
                        fieldname: 'type',
                        fieldtype:'Select',
                        options: "envelope\npackage",
                        read_only: 0,
                        reqd: 1,
                        columns: 2,
                        in_list_view: 1
                    }]
            }
        ],
        primary_action_label: 'Create Packages',
        primary_action(values) {
            console.log(values)
            frappe.call({
                method: "package_management.package_management.doctype.package.package.quick_package_creation",
                args: {
                    "customer": values.customer,
                    "packages": values.packages
                },
                btn: $('.primary-action'),
                freeze: true,
                callback: (r) => {
                    console.log(r);
                    if (r.message === 1) {
                        dialog.hide()
                    } else {

                    }

                }
            })
        }
    });
    dialog.$wrapper.on('keydown', 'input[data-fieldname="barcode"]', (e) => {
        if(e.which === 13) {
            // Stop Propagation and default event, otherwise the dialog primary action is executed.
            e.preventDefault();
            e.stopPropagation();
            // The guide number is after the first hypen, so slice it on the index of -
            let input_field = e.currentTarget
            let guide = input_field.value
            let grid = dialog.fields_dict.packages.grid;
            let df = dialog.fields_dict.packages.df;
            // There should only be one match.
            if (guide) {
                // Check is not already scanned, e.g part of df.data.array
                if (!df.data.some((x) => x.guide === guide)) {
                    df.data.push({
                        idx: df.data.length + 1,
                        guide: guide,
                        type: 'envelope'
                    })
                } else {
                    // If scanned show a warning
                    frappe.show_alert(__("Guide {0} is already in the list", [guide]))
                }
                // Clear checked items
                grid.refresh();
                input_field.value = ''
            }
        }
    });
    dialog.show();
}

frappe.listview_settings['Package'] = {
    onload: function(listview) {
        doctype = listview.doctype
        fltr.add_filter(doctype, 'state','not in', ['returned_carrier', 'delivered', 'other']);
        frappe.route.options = { "state": "origin" }
        listview.page.add_menu_item(__('Quick Entry'), function () {
            quickPackageCreation();
        });
        listview.page.add_menu_item(__('Without Destination'), function () {
            fltr.add_filter(doctype, 'destination','in', ['']);
            listview.refresh();
        });
    }
};

