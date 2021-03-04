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
			"label": _("Brand"),
			"fieldtype": "Link",
			"fieldname": "brand_name",
			"options": "Brand",
			"width": 100
		},
		{
			"label": _("Subject"),
			"fieldtype": "Data",
			"fieldname": "subject_name",
			"width": 100
		},
		{
			"label": _("Code WB"),
			"fieldtype": "Data",
			"fieldname": "nm_id",
			"width": 100
		},
		{
			"label": _("Suppliers article"),
			"fieldtype": "Data",
			"fieldname": "sa_name",
			"width": 100
		},
		{
			"label": _("Size"),
			"fieldtype": "Data",
			"fieldname": "ts_name",
			"width": 100
		},
		{
			"label": _("Barcode"),
			"fieldtype": "Data",
			"fieldname": "barcode",
			"width": 120
		},
		{
			"label": _("Qty"),
			"fieldtype": "Int",
			"fieldname": "quantity",
			"width": 100
		},
		{
			"label": _("Retail price"),
			"fieldtype": "Int",
			"fieldname": "retail_price",
			"width": 100
		},
		{
			"label": _("Amount sales Commission"),
			"fieldtype": "Int",
			"fieldname": "sale_percent",
			"width": 100
		},
		{
			"label": _("Agreed grocery discount"),
			"fieldtype": "Int",
			"fieldname": "product_discount_for_report",
			"width": 100
		},
		{
			"label": _("Supplier promo code"),
			"fieldtype": "Int",
			"fieldname": "supplier_promo",
			"width": 100
		},
		{
			"label": _("Regular customer Discount"),
			"fieldtype": "Int",
			"fieldname": "supplier_spp",
			"width": 100
		},
		{
			"label": _("Retail price, subject to the agreed discount"),
			"fieldtype": "Int",
			"fieldname": "retail_price_withdisc_rub",
			"width": 100
		},
		{
			"label": _("Commission WB"),
			"fieldtype": "Int",
			"fieldname": "retail_commission",
			"width": 100
		},
		{
			"label": _("Commission percent WB"),
			"options": "Int",
			"fieldname": "commission_percent",
			"width": 100
		},
		{
			"label": _("To transfer to the supplier"),
			"options": "Int",
			"fieldname": "for_pay",
			"width": 100
		},
		{
			"label": _("Date of sale"),
			"fieldtype": "Data",
			"fieldname": "sale_dt",
			"width": 100
		},
		{
			"label": _("Purchase price"),
			"fieldtype": "Int",
			"fieldname": "amount_purchases",
			"width": 100
		},
		{
			"label": _("Net profit"),
			"fieldtype": "Int",
			"fieldname": "net_profit",
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
			"width": 140
		},
	]

def get_data(filters):

	data = []

	wb_price_records = get_wb_price_details(filters)
	wb_logistics = get_wb_logistics(filters)
	wb_storage = get_wb_storage(filters)

	records_length = len(wb_price_records)
	average_cost_delivery = wb_logistics[0]["amount_logistics"] / records_length
	average_cost_storage = wb_storage[0]["cost_storage"] / records_length

	for record in wb_price_records:
		amount_purchases = record.amount_purchases - average_cost_delivery - average_cost_storage
		net_profit = record.for_pay - amount_purchases
		

		row = {
			"brand_name": record.brand_name,
			"subject_name": record.subject_name,
			"nm_id": record.nm_id,
			"sa_name": record.sa_name,
			"ts_name": record.ts_name,
			"barcode": record.barcode,
			"quantity": record.quantity,
			"retail_price": record.retail_price,
			"sale_percent": record.sale_percent,
			"product_discount_for_report": record.product_discount_for_report,
			"supplier_promo": record.supplier_promo,
			"supplier_spp": record.supplier_spp,
			"retail_price_withdisc_rub": record.retail_price_withdisc_rub,
			"retail_commission": record.retail_commission,
			"commission_percent": record.commission_percent,
			"for_pay": record.for_pay,
			"sale_dt": record.sale_dt,
			"amount_purchases": amount_purchases,
			"net_profit": net_profit,
			"item_code": record.item_code,
			"item_name": record.item_name
		}
		data.append(row)

	return data

def get_conditions_sales(filters):
	conditions = ''
	if filters.brand:
		conditions += "and wb_sas.brand_name = %s" %frappe.db.escape(filters.brand)

	if filters.subject:
		conditions += "and wb_sas.subject_name = %s" %frappe.db.escape(filters.subject)

	return conditions

def get_conditions_stock(filters):
	conditions = ''
	if filters.brand:
		conditions += "and wb_stock.brand = %s" %frappe.db.escape(filters.brand)

	if filters.subject:
		conditions += "and wb_stock.subject = %s" %frappe.db.escape(filters.subject)

	return conditions

def get_wb_price_details(filters):
	conditions_sales = get_conditions_sales(filters)
	from_date = "'%s'" %filters.from_date
	to_date = "'%s'" %filters.to_date
	warehouse = "%s" %frappe.db.escape(filters.warehouse)
	company = "%s" %frappe.db.escape(filters.company)

	return frappe.db.sql("""
		SELECT
			wb_sas.brand_name, wb_sas.subject_name, wb_sas.nm_id, wb_sas.sa_name, 
			wb_sas.ts_name, wb_sas.barcode, wb_sas.quantity, wb_sas.retail_price,
			wb_sas.sale_percent, wb_sas.retail_price_withdisc_rub, wb_sas.retail_commission,
			wb_sas.product_discount_for_report, wb_sas.supplier_promo, wb_sas.supplier_spp,
			wb_sas.commission_percent, wb_sas.for_pay, wb_sas.sale_dt,
			(select IFNULL(avg(sle.valuation_rate), 0)
				from `tabStock Ledger Entry` sle
				where sle.item_code = (select parent from `tabItem Barcode` where barcode = wb_sas.barcode)
				and sle.creation between {2} and {3}
				and sle.modified between {2} and {3} 
				and sle.warehouse = {0} and sle.company = {1}) amount_purchases,
			IFNULL((select item.item_code
                FROM `tabItem` item
                WHERE item.item_code = (select parent from `tabItem Barcode` where barcode = wb_sas.barcode)), 0) item_code,
            IFNULL((select item.item_name
                FROM `tabItem` item
                WHERE item.item_code = (select parent from `tabItem Barcode` where barcode = wb_sas.barcode)), 0) item_name
		FROM
			`tabWB Sales by Sales` wb_sas
		WHERE
			wb_sas.supplier_oper_name = "Продажа" and wb_sas.sale_dt between {2} and {3} {4}
	""".format(warehouse, company, from_date, to_date, conditions_sales), as_dict=1)

def get_wb_logistics(filters):
	conditions_sales = get_conditions_sales(filters)
	from_date = "'%s'" %filters.from_date
	to_date = "'%s'" %filters.to_date

	return frappe.db.sql("""
		select IFNULL(sum(wb_sas.delivery_rub), 0) as amount_logistics
		from `tabWB Sales by Sales` wb_sas
		where wb_sas.supplier_oper_name = "Логистика" and wb_sas.sale_dt between {1} and {2} {0}
	""".format(conditions_sales, from_date, to_date), as_dict=1)

def get_wb_storage(filters):
	conditions_sales = get_conditions_sales(filters)
	conditions_stock = get_conditions_stock(filters)
	from_date = "'%s'" %filters.from_date
	to_date = "'%s'" %filters.to_date
	company = "%s" %frappe.db.escape(filters.company)
	customer = "%s" %frappe.db.escape(filters.customer)

	total_qty = frappe.db.sql("""
		select IFNULL(sum(wb_sas.quantity), 0) total_qty
		from `tabWB Sales by Sales` wb_sas
		where wb_sas.supplier_oper_name = "Продажа" and wb_sas.sale_dt between {1} and {2} {0}
	"""
	.format(conditions_sales, from_date, to_date), as_dict=1)

	if filters.warehouse_storage:
		return frappe.db.sql("""
			select IFNULL(sum(car.amount_storage), 0) as cost_storage
			from `tabCommission Agent Report` car
			where car.docstatus = 1 and car.agreement_type = 'Commission'
			and car.start_date between {0} and {1}   
			and car.end_date between {0} and {1}
			and car.company = {2} and car.customer = {3}
		"""
		.format(from_date, to_date, company, customer), as_dict=1)
	else:
		stock_balance = frappe.db.sql("""
			select IFNULL(sum(wb_stock.quantity), 0) as stock_balance
			from `tabWB Stocks` wb_stock
			where wb_stock.last_change_date = {0} {1}
		"""
		.format(from_date, conditions_stock), as_dict=1)

		storage = (stock_balance[0]['stock_balance'] - total_qty[0]['total_qty'] / 7 * 60) * 0.5 * 7
		storage = [{"cost_storage": storage}]

		return storage