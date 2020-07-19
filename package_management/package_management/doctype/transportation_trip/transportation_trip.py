# -*- coding: utf-8 -*-
# Copyright (c) 2020, Lintec Tecnología and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime
from itertools import groupby
import json


# @frappe.whitelist()
# def fill_packages(packages):
#     """Fill the packages passed by the frontend that
#     the user selected"""
#     packages = json.loads(packages)
#     print(packages)


# STATE_ORDER = {
#         'planned': 1,
#         'loaded': 2,
#         'transit': 3
#         }


class TransportationTrip(Document):

    # def autofill_stops(self):
    #     """Get the unique destination/stops for the packages
    #     in the Delivery Trip"""
    #     package_dest = {p.destination for p in self.packages}
    #     # If there's no stop set It will throw and exception
    #     try:
    #         stops = {s.stop for s in self.stops}
    #     except Exception as e:
    #         stops = set()
    #     mising_stops = package_dest - stops
    #     for stop in mising_stops:
    #         self.append('stops', {
    #                    'doctype': 'Transportation Trip Stop',
    #                    'stop': stop
    #                    })

    #     return True

#    @staticmethod
#    def create_or_update_event(transportation_trip, package_name, event_type,
#                               origin=None, date=None, destination=None):
#        '''Creates or updates an event to go with a Transportation Trip
#        state'''
#        doc = frappe.get_doc(doctype='Package', name=package_name)
#        doc.weight = 3
#        doc.save()
#        return
#        # This are the events related to the provided trip
#        events = frappe.db.get_all(
#                doctype='Package Event',
#                filters={
#                    'transportation_trip': transportation_trip,
#                    'parent': package_name
#                    },
#                fields=['parent', 'type'],
#                )
#
#        # Check if any of the existing events it's out of order,
#        # Meaning It shouldn't exist because the Transportation
#        # Trip has backtracked.
#
#        # Returns the event level 1,2 or 3
#        event_level = STATE_ORDER[event_type]
#        curr_event_types = [e.type for e in events]
#        # Basically check if any of the event types are of
#        # a greater rating of a greater order than the passed
#        # if so add it to the list to delete
#        events_types_to_delete = [et for et in curr_event_types
#                                  if STATE_ORDER[et] > event_level]
#        if events_types_to_delete:
#            frappe.db.delete(doctype='Package Event',
#                             filters={
#                                 'parent': package_name,
#                                 'transportation_trip': transportation_trip,
#                                 'type': ['in', events_types_to_delete],
#                                 })
#
#        print(f"---Creating or Updating event for Package--- {package_name}")
#        if event_type not in curr_event_types:
#            # We proceed to create the event
#            # We get the parent e.g "Package"
#            doc = frappe.get_doc(doctype='Package', name=package_name)
#            # Set origin, destination and date if they weren't passed
#            if not origin:
#                origin = doc.origin
#            if not destination:
#                destination = doc.destination
#            if not date:
#                date = now_datetime()
#            # We proceed to append the event
#            print("---- Appending new Record ----")
#            # doc.append('package_event', {
#            #            'type': event_type,
#            #            'origin': origin,
#            #            'date': date,
#            #            'destination': destination,
#            #            'transportation_trip': transportation_trip,
#            #            })
#            doc.save()
#            print("MODIFIED", doc.modified)
#            print(f"--- Append completed --- doc: {doc.name} --- {doc.as_dict()}")
#        else:
#            # If the event already exists we proceed to update it
#            print("---- Updating Event ----")
#            event_name = frappe.db.get_all(
#                    doctype='Package Event',
#                    filters={
#                        'parent': package_name,
#                        'type': event_type
#                        }
#                    )
#            doc = frappe.get_doc(doctype='Package Event', name=event_name)
#            doc.origin = origin
#            doc.destination = destination
#            doc.transportation_trip: transportation_trip
#            doc.date = date
#            doc.save()

    def before_save_handle_package_events(self):
        """Create/Update the event in the Package Doctype when
        the Transportation Trip changes it's state"""
        # Check if the state has changed
        doc = frappe.get_doc(doctype='Package', name='COO-6556565')
        doc.weight = 11
        doc.save()
        return
        # if self.state != frappe.db.get_value('Transportation Trip',
        #                                      self.name, fieldname='state'):

        #     # Check if in one of the states in which we auto generate
        #     # the packages events.
        #     if self.state in STATE_ORDER.keys():
        #         for p in self.packages:
        #             self.create_or_update_event(
        #                     transportation_trip=self.name,
        #                     package_name=p.package,
        #                     event_type=self.state
        #                     )

    # def before_save_missing_or_extra_stops(self):
    #     """If there's missing stops, or stops whitout packages notify,
    #     only when the trip is on planned, or loaded."""

    #     # If not in the desire state return None
    #     if self.state not in ['planned', 'loaded']:
    #         return None

    #     # List of stops and destinations
    #     stops = [s.stop for s in self.stops]
    #     package_dest = [p.destination for p in self.packages]
    #     # Stops that are missing, and stops that are extra
    #     missing_stops = [s for s in package_dest if s not in stops]
    #     extra_stops = [s for s in stops if s not in package_dest]

    #     if extra_stops:
    #         frappe.msgprint(
    #                         title=_(f"Not Used Stops"),
    #                         msg=_(f"The following stops have no packages"
    #                               f" to be delivered {*set(extra_stops),}"))
    #     if missing_stops:
    #         frappe.msgprint(
    #                         title=_(f"Missing Stops"),
    #                         msg=_(f"The following stops are not added"
    #                               f" and some packages have it as destination "
    #                               f"{*set(missing_stops),}"))

    # def validation_no_duplicate_stop(self):
    #     """Do not allow duplicate stops"""
    #     unique_stops = set()
    #     for s in self.stops:
    #         if s.stop in unique_stops:
    #             frappe.throw(_(f"Stop {s.stop} is already in this Trip"))
    #         else:
    #             unique_stops.add(s.stop)

    def before_save(self):
        # self.before_save_missing_or_extra_stops()
        self.before_save_handle_package_events()

    # def validate(self):
    #     self.validation_no_duplicate_stop()
