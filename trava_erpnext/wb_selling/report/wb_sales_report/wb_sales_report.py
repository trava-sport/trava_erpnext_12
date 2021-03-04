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
			"fieldname": "brand",
			"options": "Brand",
			"width": 100
		},
		{
			"label": _("Subject"),
			"fieldtype": "Data",
			"fieldname": "subject",
			"width": 100
		},
		{
			"label": _("Code WB"),
			"fieldtype": "Data",
			"fieldname": "nmId",
			"width": 100
		},
		{
			"label": _("Suppliers article"),
			"fieldtype": "Data",
			"fieldname": "supplier_article",
			"width": 100
		},
		{
			"label": _("Nomenclature (Code 1C)"),
			"fieldtype": "Data",
			"fieldname": "nomenclature",
			"width": 100
		},
		{
			"label": _("Last barcode"),
			"fieldtype": "Data",
			"fieldname": "last_barcode",
			"width": 120
		},
		{
			"label": _("Number of days on the site"),
			"fieldtype": "Int",
			"fieldname": "number_days_site",
			"width": 100
		},
		{
			"label": _("Unmarketable"),
			"fieldtype": "Data",
			"fieldname": "unmarketable",
			"width": 100
		},
		{
			"label": _("Date of appearance of the illiquid"),
			"fieldtype": "Date",
			"fieldname": "date_unmarketable",
			"width": 100
		},
		{
			"label": _("Turnover rate"),
			"fieldtype": "Data",
			"fieldname": "turnover_rate",
			"width": 100
		},
		{
			"label": _("The remainder of the goods (units)"),
			"fieldtype": "Int",
			"fieldname": "remainder_goods",
			"width": 100
		},
		{
			"label": _("Current retail price(before discount)"),
			"options": "Currency",
			"fieldname": "current_retail_price",
			"width": 100
		},
		{
			"label": _("New retail price (before discount)"),
			"options": "Currency",
			"fieldname": "new_retail_price",
			"width": 100
		},
		{
			"label": _("Current discount on the site,%"),
			"fieldtype": "Int",
			"fieldname": "current_discount_site",
			"width": 100
		},
		{
			"label": _("Recommended discount,%"),
			"fieldtype": "Int",
			"fieldname": "recommended_discount",
			"width": 100
		},
		{
			"label": _("The agreed discount,%"),
			"fieldtype": "Int",
			"fieldname": "agreed_discount",
			"width": 100
		},
		{
			"label": _("Current promo code discount,%"),
			"fieldtype": "Int",
			"fieldname": "current_promo_code_discount",
			"width": 100
		},
		{
			"label": _("New promo code discount,%"),
			"fieldtype": "Int",
			"fieldname": "new_promo_code_discount",
			"width": 100
		},
		{
			"label": _("Current price with discounts"),
			"options": "Currency",
			"fieldname": "current_price_discounts",
			"width": 100
		},
		{
			"label": _("Current price with discounts and promo codes"),
			"options": "Currency",
			"fieldname": "current_price_disc_promo_code",
			"width": 100
		},
		{
			"label": _("New price with discounts"),
			"options": "Currency",
			"fieldname": "new_price_discounts",
			"width": 100
		},
		{
			"label": _("New price with discounts and promo codes"),
			"options": "Currency",
			"fieldname": "new_price_disc_promo_code",
			"width": 100
		},
		{
			"label": _("Cost"),
			"options": "Currency",
			"fieldname": "standard_price",
			"width": 100
		},
		{
			"label": _("Current net profit"),
			"options": "Currency",
			"fieldname": "current_net_profit",
			"width": 100
		},
		{
			"label": _("New net profit"),
			"options": "Currency",
			"fieldname": "new_net_profit",
			"width": 100
		},
		{
			"label": _("Desired net profit"),
			"options": "Currency",
			"fieldname": "desired_net_profit",
			"width": 100
		},
		{
			"label": _("Number of sales in the last month"),
			"fieldtype": "Int",
			"fieldname": "number_of_sales",
			"width": 100
		},
		{
			"label": _("Remains"),
			"fieldtype": "Int",
			"fieldname": "remains",
			"width": 100
		}
	]

def get_data(filters):

	data = []

	wb_price_records = get_wb_price_details(filters)

	for record in wb_price_records:

		try:
			existing_subject_delivery_cost = frappe.db.get_value("WB Deductions", 
				filters={"subject":record.subject}, fieldname="cost")
			existing_subject_remuneration = frappe.db.get_value("WB Deductions", 
				filters={"subject":record.subject}, fieldname="wb_percentage_remuneration")

			assert existing_subject_delivery_cost != None
			assert existing_subject_remuneration != None
		except Exception:
			frappe.throw(_("In the line with the value of the barcode %s, the ""subject"" field is not filled in.." % record.last_barcode))

		agreed_discount = filters.new_discount

		if not filters.calculation_new_price_discounts:
			if filters.desired_net_profit:
				agreed_discount = 100 - ((((filters.desired_net_profit + (existing_subject_delivery_cost * 2) + record.valuation_rate)
					* 100 / (100 - existing_subject_remuneration)) * 100 / (100 - record.current_promo_code_discount)) 
						* 100 / record.current_retail_price)

			if agreed_discount:
				new_price_discount = calculation_retail_price_discounts(record.current_retail_price, agreed_discount)
			else:
				new_price_discount = record.current_retail_price
			if filters.new_promo_code_discount:
				new_price_disc_promo_code = calculation_retail_price_discounts(new_price_discount, filters.new_promo_code_discount)
			else:
				new_price_disc_promo_code = new_price_discount

			new_net_profit = calculation_net_profit(new_price_disc_promo_code, record.valuation_rate,
					existing_subject_delivery_cost, existing_subject_remuneration)
		else:
			new_price_discount = new_price_disc_promo_code = new_net_profit = ""
			if filters.new_price:
				if filters.desired_net_profit:
					if filters.new_promo_code_discount:
						agreed_discount = 100 - ((((filters.desired_net_profit + (existing_subject_delivery_cost * 2) + record.valuation_rate)
							* 100 / (100 - existing_subject_remuneration)) * 100 / (100 - filters.new_promo_code_discount)) 
								* 100 / filters.new_price)
					else:
						agreed_discount = 100 - ((((filters.desired_net_profit + (existing_subject_delivery_cost * 2) + record.valuation_rate)
							* 100 / (100 - existing_subject_remuneration)) * 100 / (100 - record.current_promo_code_discount)) 
								* 100 / filters.new_price)

				if agreed_discount:
					new_price_discount = calculation_retail_price_discounts(filters.new_price, agreed_discount)
				else:
					new_price_discount = calculation_retail_price_discounts(filters.new_price, record.current_discount_site)
				if filters.new_promo_code_discount:
					new_price_disc_promo_code = calculation_retail_price_discounts(new_price_discount, filters.new_promo_code_discount)
				else:
					new_price_disc_promo_code = calculation_retail_price_discounts(new_price_discount, record.current_promo_code_discount)

				new_net_profit = calculation_net_profit(new_price_disc_promo_code, record.valuation_rate,
					existing_subject_delivery_cost, existing_subject_remuneration)

		if filter_processing_from_to(filters.new_price, filters.from_new_price, filters.to_new_price):
			continue
		
		if filter_processing_from_to(agreed_discount, filters.from_new_discount, filters.to_new_discount):
			continue

		if filter_processing_from_to(filters.new_promo_code_discount, filters.from_new_promo_code_discount, filters.to_new_promo_code_discount):
			continue

		current_price_discount = calculation_retail_price_discounts(record.current_retail_price, record.current_discount_site)

		if filter_processing_from_to(current_price_discount, filters.from_current_price_discount, filters.to_current_price_discount):
			continue

		current_price_discount_promo_code = calculation_retail_price_discounts(current_price_discount, record.current_promo_code_discount)

		if filter_processing_from_to(current_price_discount_promo_code, filters.from_current_price_discount_promo_code, 
			filters.to_current_price_discount_promo_code):
			continue

		if filter_processing_from_to(new_price_discount, filters.from_new_price_discount, filters.to_new_price_discount):
			continue

		if filter_processing_from_to(new_price_disc_promo_code, filters.from_new_price_disc_promo_code, filters.to_new_price_disc_promo_code):
			continue

		if new_net_profit:
			if filter_processing_from_to(new_net_profit, filters.from_new_net_profit, filters.to_new_net_profit):
				continue

		current_net_profit = calculation_net_profit(current_price_discount_promo_code, 
			record.valuation_rate, existing_subject_delivery_cost, existing_subject_remuneration)

		if filter_processing_from_to(current_net_profit, filters.from_current_net_profit, filters.to_current_net_profit):
			continue

		if filter_processing_from_to(record.wb_sales_qty, filters.from_sales, filters.to_sales):
			continue
		
		if filter_processing_from_to(record.wb_stocks_qty, filters.from_remnant, filters.to_remnant):
			continue 

		row = {
			"brand": record.brand,
			"subject": record.subject,
			"nmId": record.collection,
			"supplier_article": record.supplier_article,
			"nomenclature": record.nomenclature,
			"last_barcode": record.last_barcode,
			"number_days_site": record.number_days_site,
			"unmarketable": record.unmarketable,
			"date_unmarketable": record.date_unmarketable,
			"turnover_rate": record.turnover_rate,
			"remainder_goods": record.remainder_goods,
			"current_retail_price": record.current_retail_price,
			"new_retail_price": filters.new_price,
			"current_discount_site": record.current_discount_site,
			"recommended_discount": record.recommended_discount,
			"agreed_discount": agreed_discount,
			"current_promo_code_discount": record.current_promo_code_discount,
			"new_promo_code_discount": filters.new_promo_code_discount,
			"current_price_discounts": current_price_discount,
			"current_price_disc_promo_code": current_price_discount_promo_code,
			"new_price_discounts": new_price_discount,
			"new_price_disc_promo_code": new_price_disc_promo_code,
			"standard_price": record.valuation_rate,
			"current_net_profit": current_net_profit,
			"new_net_profit": new_net_profit,
			"desired_net_profit": filters.desired_net_profit,
			"number_of_sales": record.wb_sales_qty,
			"remains": record.wb_stocks_qty
		}
		data.append(row)

	return data

def filter_processing_from_to(value, from_value, to_value):
	if value and (from_value or to_value):
			if from_value and to_value:
				if value < from_value or value > to_value:
					return True
			elif from_value:
				if value < from_value:
					return True
			elif to_value:
				if value > to_value:
					return True

def calculation_retail_price_discounts(price, discount):
	calculated_price = price - (price * (discount / 100))
	return calculated_price

def calculation_net_profit(price, standard_price, existing_subject_delivery_cost, existing_subject_remuneration):
	net_profit = price - (price * (existing_subject_remuneration / 100)) - standard_price - (existing_subject_delivery_cost * 2)

	return net_profit

def get_conditions_sle(filters):
	conditions = ''
	if filters.get("warehouse"):
		conditions += "AND sle.warehouse = %s" %frappe.db.escape(filters.warehouse)

	if filters.get("company"):
		conditions += "AND sle.company = %s" %frappe.db.escape(filters.company)

	return conditions

def get_conditions_wb_sales(filters):
	conditions = ''
	if filters.get('from_date_sales'):
		conditions += "AND wb_sales.date >= '%s'" %filters.from_date_sales

	if filters.get('to_date_sales'):
		conditions += "AND wb_sales.date <= '%s'" %filters.to_date_sales

	return conditions

def get_conditions_wbs(filters):
	conditions = ''
	if filters.get('brand'):
		conditions += "AND wbs.brand = %s" %frappe.db.escape(filters.brand)

	if filters.get('unmarketable') and filters.get('unmarketable') != 'Все':
		conditions += "AND wbs.unmarketable = '%s'" %filters.unmarketable

	if filters.get("from_turnover_rate"):
		conditions += "AND wbs.turnover_rate >= %s" %frappe.db.escape(filters.from_turnover_rate)

	if filters.get("to_turnover_rate"):
		conditions += "AND wbs.turnover_rate <= %s" %frappe.db.escape(filters.to_turnover_rate)

	if filters.get("from_current_price"):
		conditions += "AND wbs.current_retail_price >= %s" %frappe.db.escape(filters.from_current_price)

	if filters.get("to_current_price"):
		conditions += "AND wbs.current_retail_price <= %s" %frappe.db.escape(filters.to_current_price)

	if filters.get("from_current_discount"):
		conditions += "AND wbs.current_discount_site >= %s" %frappe.db.escape(filters.from_current_discount)

	if filters.get("to_current_discount"):
		conditions += "AND wbs.current_discount_site <= %s" %frappe.db.escape(filters.to_current_discount)

	if filters.get("from_current_promo_code"):
		conditions += "AND wbs.current_promo_code_discount >= %s" %frappe.db.escape(filters.from_current_promo_code)

	if filters.get("to_current_promo_code"):
		conditions += "AND wbs.current_promo_code_discount <= %s" %frappe.db.escape(filters.to_current_promo_code)

	return conditions

def get_wb_price_details(filters):
	conditions_sle = get_conditions_sle(filters)
	conditions_wb_sales = get_conditions_wb_sales(filters)
	conditions_wbs = get_conditions_wbs(filters)

	return frappe.db.sql("""
		SELECT
			wbs.brand, wbs.subject, wbs.nmId, wbs.supplier_article, 
			wbs.barcode, wbs.number_days_site,
			wbs.unmarketable, wbs.date_unmarketable, wbs.turnover_rate,
			wbs.remainder_goods, wbs.current_retail_price, 
			wbs.current_discount_site, wbs.recommended_discount,
			wbs.current_promo_code_discount,
			IFNULL((SELECT sle.valuation_rate
				FROM `tabStock Ledger Entry` sle
				WHERE sle.item_code = (select parent from `tabItem Barcode` where barcode = wbs.last_barcode)
				AND sle.creation = (SELECT max(creation) FROM `tabStock Ledger Entry` sle 
				WHERE sle.item_code = (select parent from `tabItem Barcode` where barcode = wbs.last_barcode))
				AND sle.modified = (SELECT max(modified) FROM `tabStock Ledger Entry` sle 
				WHERE sle.item_code = (select parent from `tabItem Barcode` where barcode = wbs.last_barcode)) {0}), 0) valuation_rate,
			IFNULL((SELECT SUM(wb_sales.quantity)
                FROM `tabWB Sales` wb_sales
                WHERE wb_sales.supplier_article = wbs.supplier_article {1}), 0) wb_sales_qty,
            IFNULL((SELECT SUM(wb_stocks.quantity)
                FROM `tabWB Stocks` wb_stocks
                WHERE wb_stocks.supplier_article = wbs.supplier_article), 0) wb_stocks_qty
		FROM
			`tabWB Sales` wbs
		WHERE
			wbs.remainder_goods >= 0 {2}
	""".format(conditions_sle, conditions_wb_sales, conditions_wbs), as_dict=1)