import frappe
from frappe import _, msgprint
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from frappe.utils import cint

from six import iteritems


def so_dn_required(self):
	"""check in manage account if sales order / delivery note required or not."""
	if self.is_return:
		return

	agreement_type = frappe.db.get_value("Agreement", self.agreement, "agreement_type")
	if agreement_type == 'Commission':
		return

	prev_doc_field_map = {'Sales Order': ['so_required', 'is_pos'],'Delivery Note': ['dn_required', 'update_stock']}
	for key, value in iteritems(prev_doc_field_map):
		if frappe.db.get_single_value('Selling Settings', value[0]) == 'Yes':

			if frappe.get_value('Customer', self.customer, value[0]):
				continue
			
			for d in self.get('items'):
				if (d.item_code and not d.get(key.lower().replace(' ', '_')) and not self.get(value[1])):
					msgprint(_("{0} is mandatory for Item {1}").format(key, d.item_code), raise_exception=1)

def validate_with_previous_doc(self):
	agreement_type = frappe.db.get_value("Agreement", self.agreement, "agreement_type")

	if agreement_type == 'Commission':
		super(SalesInvoice, self).validate_with_previous_doc({
		"Commission Agent Report": {
			"ref_dn_field": "commission_agent_report",
			"compare_fields": [["customer", "="], ["company", "="], ["project", "="], ["currency", "="]]
		},
		"Commission Agent Report Item": {
			"ref_dn_field": "car_detail",
			"compare_fields": [["item_code", "="], ["uom", "="], ["conversion_factor", "="]],
			"is_child_table": True,
			"allow_duplicate_prev_row_id": True
		},
		"Delivery Note": {
			"ref_dn_field": "delivery_note",
			"compare_fields": [["customer", "="], ["company", "="], ["project", "="], ["currency", "="]]
		},
		"Delivery Note Item": {
			"ref_dn_field": "dn_detail",
			"compare_fields": [["item_code", "="], ["uom", "="], ["conversion_factor", "="]],
			"is_child_table": True,
			"allow_duplicate_prev_row_id": True
		},
	})
	else:
		super(SalesInvoice, self).validate_with_previous_doc({
			"Sales Order": {
				"ref_dn_field": "sales_order",
				"compare_fields": [["customer", "="], ["company", "="], ["project", "="], ["currency", "="]]
			},
			"Sales Order Item": {
				"ref_dn_field": "so_detail",
				"compare_fields": [["item_code", "="], ["uom", "="], ["conversion_factor", "="]],
				"is_child_table": True,
				"allow_duplicate_prev_row_id": True
			},
			"Delivery Note": {
				"ref_dn_field": "delivery_note",
				"compare_fields": [["customer", "="], ["company", "="], ["project", "="], ["currency", "="]]
			},
			"Delivery Note Item": {
				"ref_dn_field": "dn_detail",
				"compare_fields": [["item_code", "="], ["uom", "="], ["conversion_factor", "="]],
				"is_child_table": True,
				"allow_duplicate_prev_row_id": True
			},
		})

	if cint(frappe.db.get_single_value('Selling Settings', 'maintain_same_sales_rate')) and not self.is_return:
		if agreement_type == 'Commission':
			self.validate_rate_with_reference_doc([
			["Commission Agent Report", "commission_agent_report", "car_detail"],
			["Delivery Note", "delivery_note", "dn_detail"]
			])
		else:
			self.validate_rate_with_reference_doc([
				["Sales Order", "sales_order", "so_detail"],
				["Delivery Note", "delivery_note", "dn_detail"]
			])

def build_my_thing(w,e):
	SalesInvoice.validate_with_previous_doc = validate_with_previous_doc
	SalesInvoice.so_dn_required = so_dn_required