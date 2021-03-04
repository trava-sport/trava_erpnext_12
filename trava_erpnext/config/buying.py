from __future__ import unicode_literals
import frappe
from frappe import _

def get_data():
	return  [
		{
			"label": _("Supplier"),
			"items": [
				{
					"type": "doctype",
					"name": "Agreement",
					"description": _("Agreement"),
					"onboard": 1,
				},
			]
		},
	]