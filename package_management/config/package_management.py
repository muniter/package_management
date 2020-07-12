from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
      {
        "label": _("Package Management"),
        "icon": "octicon octicon-git-merge",
        "items": [
            {
              "type": "doctype",
              "name": "Package",
              "label": _("Package"),
              "description": _("Packages that are sent and managed"),
            },
            {
              "type": "doctype",
              "name": "Package Movement",
              "label": _("Package Movement"),
              "description": _("The moves of each package"),
            },
            {
              "type": "doctype",
              "name": "Transportation Trip",
              "label": _("Transportation Trip"),
              "description": _("The Trip each Vehicle of the Fleet does"),
            },
            {
              "type": "doctype",
              "name": "Transportation Route",
              "label": _(""),
              "description": _("The routes the Transportation Trips use"),
            },
            {
              "type": "doctype",
              "name": "Customers",
              "label": _(""),
              "description": _("The routes the Transportation Trips use"),
            },
          ]
      }
      ]
