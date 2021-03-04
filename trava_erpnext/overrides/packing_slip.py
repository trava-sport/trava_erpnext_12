# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model import no_value_fields
from erpnext.stock.doctype.packing_slip.packing_slip import PackingSlip
from frappe.utils import cint, flt


class CustomPackingSlip(PackingSlip):

	def validate(self):
		"""
			* Validate existence of submitted Delivery Note
			* Case nos do not overlap
			* Check if packed qty doesn't exceed actual qty of delivery note

			It is necessary to validate case nos before checking quantity
		"""
		self.validate_delivery_note()
		self.validate_items_mandatory()
		self.validate_case_nos()
		self.validate_qty()
		self.validate_item()

		from erpnext.utilities.transaction_base import validate_uom_is_integer
		validate_uom_is_integer(self, "stock_uom", "qty")
		validate_uom_is_integer(self, "weight_uom", "net_weight")

	def validate_qty(self):
		"""Check packed qty across packing slips and delivery note"""
		# Get Delivery Note Items, Item Quantity Dict and No. of Cases for this Packing slip
		dn_details, ps_item_qty, ps_item, no_of_cases = self.get_details_for_packing()

		for item in dn_details:
			new_packed_qty = (flt(ps_item_qty[item['item_code']]) * no_of_cases) + \
				flt(item['packed_qty'])
			if new_packed_qty > flt(item['qty']) and no_of_cases:
				self.recommend_new_qty(item, ps_item_qty, no_of_cases)

	def validate_item(self):
		"""Check packed items across packing slips and delivery note"""
		# Get Delivery Note Items, Item Quantity Dict and No. of Cases for this Packing slip
		dn_details, ps_item_qty, ps_item, no_of_cases = self.get_details_for_packing()

		delivery_note_items = [d['item_code'] for d in dn_details]
		
		for item in ps_item:
			if item not in delivery_note_items:
				self.recommend_delete_item(item)


	def get_details_for_packing(self):
		"""
			Returns
			* 'Delivery Note Items' query result as a list of dict
			* Item Quantity dict of current packing slip doc
			* No. of Cases of this packing slip
		"""

		rows = [d.item_code for d in self.get("items")]

		# also pick custom fields from delivery note
		custom_fields = ', '.join(['dni.`{0}`'.format(d.fieldname)
			for d in frappe.get_meta("Delivery Note Item").get_custom_fields()
			if d.fieldtype not in no_value_fields])

		if custom_fields:
			custom_fields = ', ' + custom_fields

		condition = ""
		if rows:
			condition = " and item_code in (%s)" % (", ".join(["%s"]*len(rows)))

		# gets item code, qty per item code, latest packed qty per item code and stock uom
		res = frappe.db.sql("""select item_code, sum(qty) as qty,
			(select sum(psi.qty * (abs(ps.to_case_no - ps.from_case_no) + 1))
				from `tabPacking Slip` ps, `tabPacking Slip Item` psi
				where ps.name = psi.parent and (ps.docstatus = 1 or ps.docstatus = 0)
				and ps.delivery_note = dni.parent and psi.item_code=dni.item_code
				and from_case_no != {from_case_no}) as packed_qty,
			stock_uom, item_name, description, dni.batch_no {custom_fields}
			from `tabDelivery Note Item` dni
			where parent=%s {condition}
			group by item_code""".format(condition=condition, custom_fields=custom_fields, from_case_no=self.from_case_no),
			tuple([self.delivery_note] + rows), as_dict=1)

		ps_item_qty = dict([[d.item_code, d.qty] for d in self.get("items")])
		ps_item = [d.item_code for d in self.get("items")]
		no_of_cases = cint(self.to_case_no) - cint(self.from_case_no) + 1

		return res, ps_item_qty, ps_item, no_of_cases


	def recommend_new_qty(self, item, ps_item_qty, no_of_cases):
		"""
			Recommend a new quantity and raise a validation exception
		"""
		item['recommended_qty'] = (flt(item['qty']) - flt(item['packed_qty'])) / no_of_cases + 1
		item['specified_qty'] = flt(ps_item_qty[item['item_code']])
		if not item['packed_qty']: item['packed_qty'] = 0

		frappe.throw(_("Quantity for Item {0} must be less than {1}").format(item.get("item_code"), item.get("recommended_qty")))

	def recommend_delete_item(self, item):
		"""
			Recommend deleting the product and raise a validation exception
		"""
		frappe.throw(_("Товар {0} отсутствует в накладной {1}. Удалите данный товар из накладной.").format(item, self.delivery_note))

