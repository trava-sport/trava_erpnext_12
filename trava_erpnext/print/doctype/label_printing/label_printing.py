# -*- coding: utf-8 -*-
# Copyright (c) 2021, trava and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class LabelPrinting(Document):
	def validate(self):
		self.validate_item()

	def validate_item(self):
		for item in self.items:
			data_item = frappe.db.get_value("Item", 
					filters={"item_code":item.item_code}, fieldname=["item_name", "article"])

			item.item_name = data_item[0]
			item.article = data_item[1]
