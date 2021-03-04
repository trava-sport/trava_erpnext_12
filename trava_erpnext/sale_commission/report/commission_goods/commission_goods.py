# Copyright (c) 2013, trava and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.utils.nestedset import get_descendants_of

def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		{
			"label": _("Customer"),
			"fieldtype": "Link",
			"fieldname": "customer",
			"options": "Customer",
			"width": 100
		},
		{
			"label": _("Item Name"),
			"fieldtype": "Data",
			"fieldname": "item_name",
			"width": 140
		},
		{
			"label": _("Item Code"),
			"fieldtype": "Link",
			"fieldname": "item_code",
			"options": "Item",
			"width": 120
		},
		{
			"label": _("UOM"),
			"fieldtype": "Link",
			"fieldname": "stock_uom",
			"options": "UOM",
			"width": 100
		},
		{
			"label": _("Handed"),
			"fieldtype": "Data",
			"fieldname": "handed_qty",
			"width": 100
		},
		{
			"label": _("Sales qty"),
			"fieldtype": "Data",
			"fieldname": "sales_qty",
			"width": 100
		},
		{
			"label": _("Sales amount"),
			"fieldtype": "Data",
			"fieldname": "sales_amount",
			"width": 100
		},
		{
			"label": _("Return"),
			"fieldtype": "Data",
			"fieldname": "return_qty",
			"width": 100
		},
		{
			"label": _("Remainder"),
			"fieldtype": "Data",
			"fieldname": "remainder_qty",
			"width": 100
		}
	]

def get_data(filters):

	data = []

	sales_order_records = get_sales_order_details(filters)

	for record in sales_order_records:
		remainder_qty = record.qty - record.car_qty - record.dn_qty
		if filters.didnt_report_back == 'Greater than zero':
			if remainder_qty == 0:
				continue
		
		if filters.didnt_report_back == 'Zero':
			if remainder_qty != 0:
				continue

		row = {
			"customer": record.customer,
			"item_name": record.item_name,
			"item_code": record.item_code,
			"stock_uom": record.uom,
			"handed_qty": record.qty,
			"sales_qty": record.car_qty,
			"sales_amount": record.amount_principal,
			"return_qty": record.dn_qty,
			"remainder_qty": remainder_qty
		}
		data.append(row)

	return data

def get_conditions_so(filters):
	conditions = ''
	if filters.get('item_group'):
		conditions += "AND so_item.item_group = %s" %frappe.db.escape(filters.item_group)

	if filters.get('on_date'):
		conditions += "AND so.transaction_date <= '%s'" %filters.on_date

	if filters.get('agreement'):
		conditions += "AND so.agreement <= '%s'" %frappe.db.escape(filters.agreement)

	if filters.get("item_code"):
		conditions += "AND so_item.item_code = %s" %frappe.db.escape(filters.item_code)

	if filters.get("customer"):
		conditions += "AND so.customer = %s" %frappe.db.escape(filters.customer)

	if filters.get("company"):
		conditions += "AND so.company = %s" %frappe.db.escape(filters.company)

	return conditions

def get_conditions_car(filters):
	conditions = ''
	if filters.get('item_group'):
		conditions += "AND car_item.item_group = %s" %frappe.db.escape(filters.item_group)

	if filters.get('on_date'):
		conditions += "AND car.transaction_date <= '%s'" %filters.on_date

	if filters.get('agreement'):
		conditions += "AND car.agreement = '%s'" %frappe.db.escape(filters.agreement)

	if filters.get("item_code"):
		conditions += "AND car_item.item_code = %s" %frappe.db.escape(filters.item_code)

	if filters.get("company"):
		conditions += "AND car.company = %s" %frappe.db.escape(filters.company)

	return conditions

def get_conditions_dn(filters):
	conditions = ''
	if filters.get('item_group'):
		conditions += "AND dn_item.item_group = %s" %frappe.db.escape(filters.item_group)

	if filters.get('on_date'):
		conditions += "AND dn.posting_date <= '%s'" %filters.on_date

	if filters.get('agreement'):
		conditions += "AND dn.agreement = '%s'" %frappe.db.escape(filters.agreement)

	if filters.get("item_code"):
		conditions += "AND dn_item.item_code = %s" %frappe.db.escape(filters.item_code)

	if filters.get("company"):
		conditions += "AND dn.company = %s" %frappe.db.escape(filters.company)

	return conditions

def get_sales_order_details(filters):
	conditions_so = get_conditions_so(filters)
	conditions_car = get_conditions_car(filters)
	conditions_dn = get_conditions_dn(filters)

	return frappe.db.sql("""
		SELECT
			so.customer, so_item.item_name, so_item.item_code, 
			so_item.uom, SUM(so_item.qty) qty,
			IFNULL((SELECT SUM(car_item.qty)
                FROM `tabCommission Agent Report` car
                LEFT JOIN `tabCommission Agent Report Item` car_item 
                ON car.name = car_item.parent
                WHERE car_item.item_code = so_item.item_code AND
                car.docstatus = 1 AND car.agreement_type = 'Commission'
				AND so.docstatus = 1 {1}), 0) car_qty,
			IFNULL((SELECT SUM(car_item.amount) - SUM(car_item.award)
                FROM `tabCommission Agent Report` car
                LEFT JOIN `tabCommission Agent Report Item` car_item 
                ON car.name = car_item.parent
                WHERE car_item.item_code = so_item.item_code AND
                car.docstatus = 1 AND car.agreement_type = 'Commission'
				AND so.docstatus = 1 {1}), 0) amount_principal,
            IFNULL((SELECT SUM(dn_item.qty)
                FROM `tabDelivery Note` dn
                LEFT JOIN `tabDelivery Note Item` dn_item 
                ON dn.name = dn_item.parent
                WHERE dn_item.item_code = so_item.item_code AND
                dn.is_return = 1 AND dn.docstatus = 1 AND
                dn.agreement_type = 'Commission'
				AND so.docstatus = 1 {2}), 0) dn_qty
		FROM
			`tabSales Order` so 
			JOIN `tabSales Order Item` so_item
			ON so.name = so_item.parent
		WHERE
			so.docstatus = 1 AND so.agreement_type = 'Commission' {0}
		GROUP BY
			so_item.item_code
	""".format(conditions_so, conditions_car, conditions_dn), as_dict=1)