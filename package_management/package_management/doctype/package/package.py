# -*- coding: utf-8 -*-
# Copyright (c) 2020, Lintec Tecnología and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import now_datetime
import collections

from frappe.model.document import Document


# @frappe.whitelist()
# def get_available_packages_for_trip(*args):
#     print("Getting called")
#     print(args)
#     docs = args
#     docs = frappe.get_all("Package",
#                           filters={'state': 'origin'},
#                           fields=['name', 'destination'])
#     return docs


class Package(Document):

    pass
    # def validate_check_dupliate(self):

    #     same_guide = frappe.get_all(
    #         doctype='Package',
    #         filters={'guide': self.guide, 'name': ['!=', self.name]},
    #         fields=['name', 'guide', 'amended_from']
    #         )

    #     if same_guide:
    #         # Check the current amended_from comes from the duplicate
    #         duplicate = same_guide[0]
    #         if self.amended_from == duplicate.name:
    #             return None
    #         else:
    #             frappe.throw(_(
    #                             f"The guide number {self.guide} already "
    #                             f"exists on the system in the package "
    #                             f"{duplicate.name}"
    #                         ))

    # def validate_delivery_date(self):
    #     if not self.delivery_date and self.state == 'delivered':
    #         frappe.throw(_("Set delivery date to set package as delivered"))
    #     elif self.delivery_date and not self.state == 'delivered':
    #         frappe.throw(_("Set the package as delivered\
    #                         to set the delivery date"))

    # def validate_event_for_state(self):
    #     events = [e.type for e in self.package_event]
    #     if self.state not in events:
    #         frappe.throw(_(
    #                        f"To set the state as {self.state} and event "
    #                        f"of type {self.state} must be created first"
    #                      ))

    # def validate_no_duplicate_event_per_transportation_trip(self):
    #     '''Check for no duplicate events per transportation Trip'''

    #     trans_trips = [e.transportation_trip for e in self.package_event
    #                    if e.transportation_trip]
    #     trip_with_duplicate = set([t for t in trans_trips
    #                                if trans_trips.count(t) > 1])
    #     if trip_with_duplicate:
    #         frappe.throw(_(f"Duplicate event per Transportation Trip"
    #                        f": {', '.join(trip_with_duplicate)}"))

    # def validate_sort_events(self):
    #     '''Sort the child table package_event'''
    #     # TODO this is not sorting anython since is
    #     # Not assigning
    #     sequence = range(1, len(self.package_event)+1)
    #     sorted_events = self.package_event
    #     sorted_events.sort(key=lambda x: x.date)
    #     for e, i in zip(sorted_events, sequence):
    #         e.idx = i


    # def before_save_state(self):
    #     """This method takes care of the state
    #     field logic"""
    #     pass

    # def before_save_delivery_or_return_event(self):
    #     '''Deal with end event, in case is done manually'''
    #     if self.state in ['delivered', 'returned', 'returned_carrier']:
    #         # Get all the event types
    #         events = [e.type for e in self.package_event]

    #         # If there's not an event for this state
    #         # Let's create it otherwise do nothing
    #         if self.state not in events:
    #             # Set the proper date
    #             if self.delivery_date:
    #                 # If delivery date is set
    #                 date = self.delivery_date
    #             else:
    #                 date = now_datetime()

    #             if self.state == 'delivered':
    #                 # Set the proper destination
    #                 destination = self.destination
    #             else:
    #                 # If it was returned or to carrier just set the origin
    #                 destination = self.origin

    #             self.append('package_event', {
    #                         'doctype': 'Package Event',
    #                         'type': self.state,
    #                         'origin': self.origin,
    #                         'date': date,
    #                         'destination': destination
    #                         })
    #         else:
    #             return

    # def validate_create_origin_event(self):
    #     # Check if there's an origin event
    #     origin = [doc for doc in self.package_event if doc.type == 'origin']
    #     if not origin:
    #         # Create origin event when creating the package
    #         a = self.append('package_event', {
    #             'doctype': 'Package Event',
    #             'type': 'origin',
    #             'origin': self.origin,
    #             'date': self.received_date,
    #             'destination': self.origin
    #             })
    #         # print(a.as_dict())

    # def before_insert_received_date(self):
    #     # Check if there's a received date
    #     # If not set the now datetime
    #     if not self.received_date:
    #         self.received = now_datetime()

    # def autoname(self):
    #     """Covers when the guide or the company changes name
    #     and shortens the company name so it isn't too long"""
    #     if self.customer != frappe.db.get_value('Package',
    #             self.name, fieldname='customer')\
    #     or self.guide != frappe.db.get_value('Package',
    #             self.name, fieldname='guide'):
    #         customer = self.customer
    #         # Customer name abbreviation
    #         if len(customer) > 3:
    #             customer = customer[0:3].upper()

    #         title = f"{customer}-{self.guide}"
    #         # The naming series is the title field
    #         self.title = title
    #         # If name not what It should be
    #         # Then we rename
    #         if self.name != title:
    #             frappe.rename_doc("Package",
    #                               self.name, title, ignore_permissions=True)
    #         else:
    #             self.name = title

    # def before_insert(self):
    #     self.before_insert_received_date()

    # def before_save(self):
    #     pass

    # def validate(self):
    #     self.validate_check_dupliate()
    #     self.validate_delivery_date()
    #     self.validate_create_origin_event()
    #     self.validate_event_for_state()
    #     # self.validate_no_duplicate_event_per_transportation_trip()
    #     self.validate_sort_events()

    # def on_update(self):
    #     # It's only called when a documents values
    #     # have changed
    #     self.autoname()

    # def before_submit(self):
    #     if self.delivery_date:
    #         return
    #     else:
    #         frappe.throw(_("Set delivery date before\
    #                 submitting the document."))

    #         if self.state not in ['deilvered', 'returned']:
    #             frappe.throw(_("Set package as delivered or returned\
    #                     before submitting the document."))
