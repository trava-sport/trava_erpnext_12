# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "Trava ERPNext",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Trava ERPNext")
		},
		{
			"module_name": "Agreement",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Agreement")
		},
		{
			"module_name": "Commission Agent Report",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Commission Agent Report")
		},
		{
			"module_name": "Trava Integrations",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Trava Integrations")
		},
		{
			"module_name": "WB Selling",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("WB Selling")
		}
	]
