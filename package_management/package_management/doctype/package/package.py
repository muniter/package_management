# -*- coding: utf-8 -*-
# Copyright (c) 2020, Lintec Tecnología and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from . import fetch
import frappe
from frappe import _
from frappe.utils import now_datetime
import collections
import json

from frappe.model.document import Document


STATE_LEVELS = {
        "origin": 1,
        "transfer": 1,
        "returned": 1,
        "planned": 2,
        "loaded": 2.1,
        "transit": 2.2,
        "completed": 3,  # For the TransportationTrip
        "delivered": 3,
        "returned_carrier": 3,
        "other": 3
        }


@frappe.whitelist()
def quick_package_creation(customer, packages):
    '''Method that takes care of validating and
    creating packages on custom dialog, by passing
    only guide, customer, type.'''
    packages = json.loads(packages)
    # Filter empty or incomplete rows
    packages = list(filter(
            lambda x: "guide" in x
            and "type" in x
            and x["guide"] != ""
            and x["type"] != "", packages))
    if not any(packages):
        frappe.msgprint(_("No packages values provided, try again"))
        return

    # Check if no packages is duplicate.
    duplicates = frappe.db.get_all(
            doctype='Package',
            filters={
                "guide": ['in'] + [p["guide"] for p in packages]
            },
            fields=["name", "guide"]
            )
    if any(duplicates):
        duplicates = [p.name for p in duplicates]
        frappe.throw(_("Duplicate packages {0}".format(", ".join(duplicates))))
    else:
        received_date = now_datetime()
        origin = frappe.db.get_single_value(
                'Package Management Settings',
                'default_origin')
        print("-----my-----", origin)
        counter = 0
        for p in packages:
            counter += 1
            doc = frappe.new_doc('Package')
            doc.guide = p["guide"]
            doc.type = p["type"]
            doc.customer = customer
            doc.received_date = received_date
            doc.origin = origin
            doc.save()

        frappe.msgprint(_("Created {0} packages".format(counter)))
        return 1


def fetch_package_info(packages=[]):
    print("RUNNING FETCH PACKAGE")
    if not any(packages):
        packages = frappe.db.get_all(
                doctype='Package',
                filters={
                    'fetchable': True,
                    'to_fetch': True,
                    },
                fields=['name', 'guide', 'customer'])

    print("Fetching packages", packages)
    # Get the different companies since the fetching is different
    # Dictionary with customer name, customer_id
    customers = {p.customer for p in packages}
    customers = {
            c: frappe.get_doc('Package Management Customer', c).customer_id
            for c in customers
        }

    for customer, customer_id in customers.items():
        tofetch = list(filter(lambda p: p.customer == customer, packages))
        method = getattr(fetch, f'{customer_id}_fetch', False)
        if callable(method):
            # If there's actually a method let's get the whole
            # package object and pass it to the fetch function.
            tofetch = list(map(
                lambda p: frappe.get_doc('Package', p.name), tofetch
                ))
            method(tofetch)
            return True
        else:
            print(f"No method fetch found for customer {customer}")


class Package(Document):

    def fetch_package(self):
        print("Calling fetch_package")
        result = fetch_package_info([self])
        if result:
            return True

    def can_be_fetched(self):
        '''Determines if a package can be fetched or not, meaning a method
        to fetch it exists.'''
        customer = frappe.get_doc('Package Management Customer', self.customer)
        customer_id = customer.customer_id
        method = getattr(fetch, f'{customer_id}_fetch', False)
        if method:
            return True
        else:
            return False

    def validate_check_dupliate(self):

        same_guide = frappe.db.get_all(
            doctype='Package',
            filters={'guide': self.guide, 'name': ['!=', self.name]},
            fields=['name', 'guide']
            )

        if same_guide:
            # Check the current amended_from comes from the duplicate
            duplicate = same_guide[0]
            if self.amended_from == duplicate.name:
                return None
            else:
                frappe.throw(_("The guide number {0} already exists on the system in the package {1}".format(self.guide, duplicate.name)))

    def validate_delivery_date(self):
        '''If no delivery date and package in END_STATES e.g level 3
        throw and exception, if package is not in END_STATES
        remove the delivery date'''
        if STATE_LEVELS[self.state] == 3 and not self.delivery_date:
            frappe.throw(_(f"Set delivery date to set package as {0}".format(self.state)))

    def validate_event_for_state(self):
        events = [e.type for e in self.events]
        if self.state not in events:
            frappe.throw(_("To set the state as {0} and event of type {0} must be created first".format(self.state)))

    def validate_no_duplicate_event_type_per_transporation_trip(self):
        '''Check for no duplicate events type per transportation Trip'''

        trans_trips = {e.transportation_trip for e in self.events
                       if e.transportation_trip}

        for t in trans_trips:
            events = [e.type for e in self.events
                      if e.transportation_trip == t]
            if len(events) != len(set(events)):
                frappe.throw(_("Duplicate event type for Trip {0} in Package {1}".format(t, self.name)))

    def validate_no_duplicate_end_event_type_per_transporation_trip(self):
        '''Check for no duplicate end events type per transportation Trip'''

        events = self.events
        trans_trips = {e.transportation_trip for e in self.events
                       if e.transportation_trip}

        for t in trans_trips:
            # Only capture end events, level 3
            end_events = list(filter(lambda e: e.is_end_event and e.transportation_trip == t, events))
            if len(end_events) > 1:
                frappe.throw(_("Duplicate end event type for Trip {0} in Package {1}".format(t, self.name)))

    def validate_sort_events(self):
        '''Sort the child table events'''
        sequence = range(1, len(self.events)+1)
        sorted_events = self.events
        sorted_events.sort(key=lambda x: x.date)
        for e, i in zip(sorted_events, sequence):
            e.idx = i

    def before_save_delivery_or_return_event(self):
        '''Deal with end event, in case is done manually'''
        # TODO: Repurpose for a form button action, And a list action
        if self.state in ['delivered', 'returned',
                          'returned_carrier', 'other']:
            # Get all the event types
            events = [e.type for e in self.events]

            # If there's not an event for this state
            # Let's create it otherwise do nothing
            if self.state not in events:
                # Set the proper date
                if self.delivery_date:
                    # If delivery date is set
                    date = self.delivery_date
                else:
                    date = now_datetime()

                if self.state == 'delivered':
                    # Set the proper destination
                    destination = self.destination
                else:
                    # If it was returned or to carrier just set the origin
                    destination = self.origin

                self.append('events', {
                            'doctype': 'Package Event',
                            'type': self.state,
                            'origin': self.origin,
                            'date': date,
                            'destination': destination
                            })

    def validate_create_origin_event(self):
        # Check if there's an origin event
        origin = [doc for doc in self.events if doc.type == 'origin']
        if not origin:
            # Create origin event when creating the package
            self.append('events', {
                'doctype': 'Package Event',
                'type': 'origin',
                'origin': self.origin,
                'date': self.received_date,
                'destination': self.origin
                })

    def validate_dates(self):
        # Check if there's a received date
        # If not set the now datetime
        if self.delivery_date:
            if self.received_date > self.delivery_date:
                frappe.throw(_("Delivery date must be later than received date"))

    def validate_update_state(self):
        """This method takes care of the state field logic,
        takes adventage of table elements being sorted already
        and also sets delivery date if state is in END_STATES"""
        db_state = frappe.db.get_value('Package', self.name, 'state')
        # If state has been changed manually don't trigger
        if self.state != db_state:
            return
        else:
            last_item = max(self.events, key=lambda x: x.idx, default=0)
            # Set delivery date as event date if no delivery date set
            if STATE_LEVELS[last_item.type] == 3 and not self.delivery_date:
                self.delivery_date = last_item.date
            # Remove deliver date if new state is not in END_STATES
            elif STATE_LEVELS[last_item.type] < 3 and self.delivery_date:
                self.delivery_date = ''
            # Set the state as the last item type
            self.state = last_item.type

    def validate_completed(self):
        '''Method that takes care of the completed field logic
        be automatic but allow overriding'''
        bs_self = self.get_doc_before_save()
        if bs_self and self.completed != bs_self.completed:
            return
        else:
            last_item = max(self.events, key=lambda x: x.idx, default=0)
            self.completed = True if STATE_LEVELS[last_item.type] == 3 else False

    def autoname(self):
        """If field is new sets the name, if fields that set
        the name have changed, renames"""
        # Get the name the record should have
        name = self.get_name()
        # If it doesn't exist, e.a Is a new record
        # Name it and end it
        if not frappe.db.exists('Package', self.name):
            self.name = name
            return
        else:
            if self.name != self.get_name():
                frappe.rename_doc("Package",
                                  self.name, name, ignore_permissions=True)

    def get_name(self):
        '''Method that returns the record name'''
        customer = self.customer
        if len(customer) > 3:
            customer = customer[0:3].upper()

        return f"{customer}-{self.guide}"

    def before_save(self):
        pass

    def validate_fetch(self):
        '''Check if the package can be fetch, and set the proper status'''
        if self.can_be_fetched():
            self.fetchable = True
            self.tofetch = True
        else:
            self.fetchable = False
            self.tofetch = False

    def validate(self):
        self.validate_dates()
        self.validate_check_dupliate()
        self.validate_create_origin_event()
        self.validate_no_duplicate_event_type_per_transporation_trip()
        self.validate_no_duplicate_end_event_type_per_transporation_trip()
        self.validate_sort_events()
        self.validate_update_state()
        self.validate_completed()
        self.validate_event_for_state()
        self.validate_delivery_date()
        self.validate_fetch()

    def on_update(self):
        self.autoname()
