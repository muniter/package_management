# Copyright (c) 2020, Lintec Tecnología and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from package_management.package_management.doctype.package import package
from frappe.model.document import Document
from frappe.utils import now_datetime
from itertools import groupby


STATE_ORDER = {
        'planned': 1,
        'loaded': 2,
        'transit': 3
        }

STATE_LEVELS = package.STATE_LEVELS


@frappe.whitelist()
def update_package_fields(packages):
    """This method will be called from the client to update the package
    to_collect and destination and destination from Transportation
    Trip Packages"""
    packages = json.loads(packages)
    print("Passed from the frontend", packages, "Type of it", type(packages))
    for p in packages:
        doc = frappe.get_doc('Package', p["package"])
        destination = p["destination"]
        to_collect = p["to_collect"]
        save = False
        # No empty destination
        if destination and doc.destination != destination:
            doc.destination = destination
            save = True
        if doc.to_collect != to_collect:
            doc.to_collect = to_collect
            save = True
        if save:
            doc.save()


class TransportationTrip(Document):

    def autofill_stops(self):
        """Get the unique destination/stops for the packages
        in the Delivery Trip"""
        package_dest = {p.destination for p in self.packages}
        # If there's no stop set It will throw and exception
        print("Calling atuofill stops")
        try:
            stops = {s.stop for s in self.stops}
        except Exception as e:
            stops = set()
        mising_stops = package_dest - stops
        for stop in mising_stops:
            self.append('stops', {
                       'doctype': 'Transportation Trip Stop',
                       'stop': stop
                       })

    def _get_changed_packages(self):
        '''Returns a tuple with sets of Transportation Trip Packages in format
        (added, removed, modified)'''
        # This method works with the actual packagage field, not the name of
        # the Transportation Trip Package.
        bs_self = self.get_doc_before_save()
        if bs_self:
            def hash_packages(object):
                return {(
                    x.name,
                    x.package,
                    x.destination,
                    x.to_collect,
                    x.end_event,
                    x.end_destination,
                    x.return_code
                    ) for x in object}

            bs_hashed = hash_packages(bs_self.packages)
            hashed = hash_packages(self.packages)
            modified = hashed - bs_hashed
            # Only the ttpackage name to apply the following filter
            print("Pre returned modified", modified)
            modified = [p[0] for p in modified]
            modified = tuple(filter(lambda p: p.name in modified, self.packages))
            # Sets with the names.
            bs_packages = {p.package for p in bs_self.packages}
            packages = {p.package for p in self.packages}
            # Removed packages names
            removed = (bs_packages - packages)
            added = (packages - bs_packages)
            # Replace the names with the package object it self.
            removed = tuple(filter(lambda p: p.package in removed, bs_self.packages))
            added = tuple(filter(lambda p: p.package in added, self.packages))
            print("Returned value", added, removed, modified)
            return added, removed, modified
        else:
            return tuple(self.packages), (), tuple(self.packages)

    def create_end_events(self, packages):
        '''Create the end_event set in each Package for the
        Transportation Trip'''
        date = now_datetime()
        tt_packages = filter(lambda x: x.end_event, packages)
        for p in tt_packages:
            doc = frappe.get_doc('Package', p.package)

            # Previously delete other end type events on this TT.
            end_event_tt = filter(
                    lambda p: p.transportation_trip == self.name
                    and p.is_end_event,
                    doc.events)
            [doc.remove(row) for row in end_event_tt]

            destination = p.end_destination or doc.destination
            doc.append('events', {
                       'doctype': 'Package Event',
                       'type': p.end_event,
                       'origin': doc.origin,
                       'destination': destination,
                       'return_code': p.return_code,
                       'date': date,
                       'transportation_trip': self.name,
                       'is_end_event': True,
                       })
            doc.save(ignore_permissions=True)

    def create_or_update_event(self, packages, event_type, update=True,
                               origin=None, date=None, destination=None):
        '''Creates or updates an event to go with a Transportation Trip
        state'''
        transportation_trip_level = STATE_LEVELS[event_type]
        if transportation_trip_level == 3:
            self.create_end_events(packages)
        else:
            date = date or now_datetime()
            for package in packages:
                doc = frappe.get_doc('Package', package.package)
                events = [row for row in doc.events
                          if row.transportation_trip == self.name]

                # Delete all events of higher level than current TT State level
                remove = filter(lambda x: STATE_LEVELS[x.type] > transportation_trip_level
                                or STATE_LEVELS[x.type] == 1, events)
                [doc.remove(row) for row in remove]

                # Setting up values
                origin = origin or doc.origin
                destination = destination or doc.destination

                event_for_type = next(filter(lambda e:
                                             e.type == event_type, events), None)

                # If event of the type exists update it if the flag is set.
                if event_for_type and update:
                    event = event_for_type
                    event.transportation_trip = self.name
                    event.origin = origin
                    event.destination = destination
                    event.date = date
                elif not event_for_type:
                    # Since it doesn't exist let's create it
                    doc.append('events', {
                               'doctype': 'Package Event',
                               'type': event_type,
                               'origin': origin,
                               'date': date,
                               # 'idx': 2,
                               'destination': destination,
                               'transportation_trip': self.name,
                               })
                # After all save
                doc.save(ignore_permissions=True)

    def delete_events_for_removed_packages(self, packages):
        '''Delete the packages events related to this transportation trip
        if the package has been deleted from the trip'''

        for package in packages:
            doc = frappe.get_doc('Package', package.package)
            to_remove = [row for row in doc.events
                         if row.transportation_trip == self.name]
            print("To remove:", [f"{x.parent}-{x.type}" for x in to_remove])
            [doc.remove(row) for row in to_remove]
            doc.save(ignore_permissions=True)

    def before_save_all_packages_destination(self):
        '''Make sure all packages have destination before saving'''
        for p in self.packages:
            missing_destination = [p.package for p in self.packages
                                   if not p.destination]
            if any(missing_destination):
                frappe.throw(_("All packages must have a destination, the following packages do not have it {0} ".format(", ".join(missing_destination))))

    def before_save_no_duplicate_or_empty_package(self):
        """Do not allow duplicate package"""
        unique_packages = set()
        for p in self.packages:
            if not p.package:
                frappe.throw(_("There are empty package lines delete please"))
            if p.package in unique_packages:
                frappe.throw(_("Package {0} is already in this Trip".format(p.package)))
            else:
                unique_packages.add(p)

    def validate_missing_or_extra_stops(self):
        """If there's missing stops, or stops whitout packages notify,
        only when the trip is on planned, or loaded."""

        # If not in the desire state return None
        if self.state not in ['planned', 'loaded']:
            return None

        # List of stops and destinations
        # Make sure stop is defined.
        stops = {s.stop for s in self.stops if s.stop}
        package_dest = {p.destination for p in self.packages if p.destination}
        # Stops that are missing, and stops that are extra
        missing_stops = package_dest - stops
        extra_stops = stops - package_dest

        if extra_stops:
            frappe.msgprint(
                title=_("Not Used Stops"),
                msg=_(f"The following stops have no packages to be"
                      f"delivered {', '.join(extra_stops)}"))
        if missing_stops:
            frappe.msgprint(
                title=_("Missing Stops"),
                msg=_(f"The following stops are not added and some packages "
                      f"have it as destination {', '.join(missing_stops)}"))

    def validate_no_duplicate_stop(self):
        """Do not allow duplicate stops"""
        unique_stops = set()
        for s in self.stops:
            if s.stop in unique_stops:
                frappe.throw(_("Stop {0} is already in this Trip".format(s.stop)))
            else:
                unique_stops.add(s.stop)

    def validate_no_duplicate_package(self):
        """Do not allow duplicate package"""
        unique_packages = set()
        for p in self.packages:
            if p.package in unique_packages:
                frappe.throw(_("Package {0} is already in this Trip".format(p.package)))
            else:
                unique_packages.add(p.package)

    def validate_package_correct_state(self):
        '''Make sure added packages are in ther right
        state, to avoid having an incorret state  package
        added to a transportation trip'''
        added = self._get_changed_packages()[0]
        if any(added):
            incorret_state = [
                    p.package for p in added if
                    STATE_LEVELS[
                        frappe.get_doc('Package', p.package).state] != 1]
            if any(incorret_state):
                frappe.throw(_('Packages {0} are not available to be in Transportation Trip'.format(', '.join(incorret_state))))

    def validate_handle_package_events(self):
        """Create/Update the event in the Package Doctype when
        the Transportation Trip changes it's state"""
        bs_self = self.get_doc_before_save()
        # Sends back a tuple
        added, removed, modified = self._get_changed_packages()
        completed = self.state != 'completed'
        state_changed = bs_self and bs_self.state != self.state

        # If the state changed upate the events
        # otherwise just creation
        update = state_changed

        # If the state changed run in all
        if state_changed:
            self.create_or_update_event(
                    packages=self.packages,
                    event_type=self.state,
                    update=update
                    )
        # Else If any package has been modified including the
        # added create or update
        elif any(modified):
            self.create_or_update_event(
                    packages=modified,
                    event_type=self.state,
                    update=update
                    )
        # If any package has been removed remove it's events
        if any(removed):
            self.delete_events_for_removed_packages(removed)

    def on_update(self):
        pass

    def before_save(self):
        self.before_save_no_duplicate_or_empty_package()
        self.before_save_all_packages_destination()

    def validate(self):
        self.validate_missing_or_extra_stops()
        self.validate_no_duplicate_package()
        self.validate_no_duplicate_stop()
        self.validate_package_correct_state()
        self.validate_handle_package_events()

    def on_trash(self):
        '''This method should prevent deleting because there are events
        done in the execution of the Transportation Trip as delivery
        transfer, returned, etc. And in case there's not, delete the
        events that can actually be deleted because are of type
        planned, loaded, transit'''
        end_type_events = frappe.db.get_all(
                doctype='Package Event',
                filters={
                    'transportation_trip': self.name,
                    'type': ['not in', list(STATE_ORDER.keys())]
                    },
                fields=["name", "parent", "type"]
                )

        # If there are events that should not be deleted programtically
        if any(end_type_events):
            errors = map(lambda x: f"{x.parent} - {x.type}", end_type_events)
            frappe.throw(_("There are package events that are associated with this Transportation Trip that will change the packages from Delivered, Returned etc, back to origin \nPackages:\n{0}".format(''.join(errors))),
                         title="Error"
                         )
        else:
            for p in self.packages:
                doc = frappe.get_doc('Package', p.package)
                events = doc.events
                delete = list(filter(
                        lambda e: e.transportation_trip == self.name, events))
                [doc.remove(row) for row in delete]
                doc.save(ignore_permissions=True)
