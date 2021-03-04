# -*- coding: utf-8 -*-
# Copyright (c) 2020, trava and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
import frappe
from frappe.utils import getdate
from frappe import _

class Agreement(Document):
	def validate(self):
		self.validate_period_date()

	def validate_period_date(self):
		if self.start_date and self.end_date:
			if getdate(self.start_date) > getdate(self.end_date):
				frappe.msgprint(_("Expected Start Date should be after End Date"),
					indicator='orange', title=_('Warning'))
