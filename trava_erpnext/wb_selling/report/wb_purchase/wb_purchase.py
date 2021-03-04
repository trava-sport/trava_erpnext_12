# Copyright (c) 2013, trava and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from datetime import date, datetime, timedelta
from frappe import _
from frappe.utils import flt, add_to_date, add_days
from frappe.utils.nestedset import get_descendants_of

def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	return [
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
			"label": _("Barcode"),
			"fieldtype": "Data",
			"fieldname": "barcode",
			"width": 120
		},
		{
			"label": _("Sales qty"),
			"fieldtype": "Data",
			"fieldname": "sales_qty",
			"width": 100
		},{
			"label": _("Remainder"),
			"fieldtype": "Data",
			"fieldname": "remainder_qty",
			"width": 100
		},
		{
			"label": _("Qty required to purchase"),
			"fieldtype": "Data",
			"fieldname": "purchase_goods",
			"width": 100
		},
	]

def get_data(filters):

	data = []

	sales_order_records = get_sales_order_details(filters)

	for record in sales_order_records:
		if not record.barcode:
			purchase_goods = 0
		else:
			purchase_goods = purchase_formula(record, filters)

		row = {
			"item_name": record.item_name,
			"item_code": record.item_code,
			"stock_uom": record.stock_uom,
			"barcode": record.barcode,
			"sales_qty": record.wb_sales_qty,
			"remainder_qty": record.wb_stocks_qty,
			"purchase_goods": purchase_goods
		}
		data.append(row)

	return data

def purchase_formula(record, filters):
	average_sales = record.wb_sales_qty / filters.delta_days
	sales_forecast = average_sales * get_coefficients_seasonality(record, filters)
	days_until_next_purchase = filters.days_until_next_purchase
	insurance_stock = sales_forecast * days_until_next_purchase
	days_from_purchase_to_delivery = filters.days_from_purchase_to_delivery
	product_balances_delivery_date = record.wb_stocks_qty - average_sales * days_from_purchase_to_delivery
	purchase_goods = insurance_stock - product_balances_delivery_date

	return purchase_goods

def get_coefficients_seasonality(record, filters):
	months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	data_purchase = date.today()
	data_delivery = data_purchase + timedelta(days=(filters.days_until_next_purchase + filters.days_from_purchase_to_delivery))
	date_next_purchase = data_delivery + timedelta(days=(filters.days_until_next_purchase + filters.days_from_purchase_to_delivery))
	period_purchase = str(months[date_next_purchase.month - 1]) + " " + str(date_next_purchase.year)
	period_delivery = str(months[data_delivery.month - 1]) + " " + str(data_delivery.year)

	if period_purchase == period_delivery:
		coefficients_seasonality = coefficients_seasonality(record, data_delivery)
	else:
		coefficients_seasonality_one = get_coefficients_season(record, data_delivery)
		coefficients_seasonality_two = get_coefficients_season(record, date_next_purchase)
		coefficients_seasonality = (coefficients_seasonality_one + coefficients_seasonality_two) / 2

	return coefficients_seasonality

def get_coefficients_season(record, data):
	from_date = data.replace(day=1)
	from_date = add_to_date(from_date, years=-1, months=-1)
	period_end_date = add_to_date(from_date, months=1, days=-1)

	from_sales_previous_period = get_sales_previous_period(record, from_date, period_end_date)
	if not from_sales_previous_period[0]["total_qty"]:
		coefficients_seasonality = 1
		return coefficients_seasonality

	from_date = add_days(period_end_date, 1)
	period_end_date = add_to_date(from_date, months=1, days=-1)

	to_sales_previous_period = get_sales_previous_period(record, from_date, period_end_date)
	if not to_sales_previous_period[0]["total_qty"]:
		coefficients_seasonality = 1
		return coefficients_seasonality

	coefficients_seasonality = to_sales_previous_period[0]['total_qty'] / from_sales_previous_period[0]['total_qty']

	return coefficients_seasonality

def get_sales_previous_period(record, from_date, period_end_date):
	from_date = "'%s'" %from_date
	to_date = "'%s'" %period_end_date
	barcode = "%s" %frappe.db.escape(record.barcode)

	return frappe.db.sql("""
		select IFNULL(sum(wb_sas.quantity), 0) total_qty
		from `tabWB Sales by Sales` wb_sas
		where wb_sas.supplier_oper_name = "Продажа" and wb_sas.sale_dt between {1} and {2}
		and wb_sas.barcode = {0}
	"""
	.format(barcode, from_date, to_date), as_dict=1)

def get_sales_order_details(filters):
	data_to = date.today()
	data_from = data_to + timedelta(days=-filters.delta_days)
	from_date = "'%s'" %data_from
	to_date = "'%s'" %data_to
	brand = ''
	if filters.brand:
		brand = "and item.brand = %s" %frappe.db.escape(filters.brand)

	return frappe.db.sql("""
		select item.item_code, item.stock_uom,
		(select barcode from `tabItem Barcode` where parent = item.item_code) barcode,
		IFNULL((select SUM(wb_sales.quantity)
			from `tabWB Sales` wb_sales
			where wb_sales.barcode = (select barcode from `tabItem Barcode` where parent = item.item_code) 
			and wb_sales.date between {1} and {2}), 0) wb_sales_qty,
		IFNULL((select SUM(wb_stocks.quantity)
			from `tabWB Stocks` wb_stocks
			where wb_stocks.barcode = (select barcode from `tabItem Barcode` where parent = item.item_code)
			and wb_stocks.last_change_date = {1}), 0) wb_stocks_qty
		from `tabItem` item
		where item.has_variants = 0 {0}
	""".format(brand, from_date, to_date), as_dict=1)