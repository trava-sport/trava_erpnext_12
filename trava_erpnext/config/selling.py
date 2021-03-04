from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Commission Agent Report"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Commission Agent Report",
					"description": _("Commission Agent Report"),
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Commission Goods",
					"doctype": "Commission Agent Report",
					"onboard": 1,
				},
			]
		},
		{
			"label": _("Sales"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Agreement",
					"description": _("Agreement"),
					"onboard": 1,
				},
			]
		},
		{
			"label": _("Label Printing"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Label Printing",
					"description": _("Label Printing"),
					"onboard": 1,
				},
			]
		},
	]
