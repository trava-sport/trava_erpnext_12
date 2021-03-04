# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, scrub
from frappe.utils import getdate, flt, add_to_date, add_days, date_diff
from six import iteritems
from erpnext.accounts.utils import get_fiscal_year

def execute(filters=None):
	return Analytics(filters).run()

class Analytics(object):
	def __init__(self, filters=None):
		print('filters:', filters)
		self.filters = frappe._dict(filters or {})
		self.validate_filters()
		self.date_field = 'transaction_date' \
			if self.filters.doc_type in ['Sales Order', 'Purchase Order'] else 'posting_date'
		self.months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
		self.get_period_date_ranges()

	def run(self):
		print('RUN')
		self.get_columns()
		print(self)
		self.get_data()
		self.get_chart_data()

		# Skipping total row for tree-view reports
		skip_total_row = 0

		if self.filters.tree_type in ["Supplier Group", "Item Group", "Customer Group", "Territory"]:
			skip_total_row = 1

		return self.columns, self.data, None, self.chart, None, skip_total_row

	def validate_filters(self):
		from_date, to_date = self.filters.get("from_date"), self.filters.get("to_date")

		if date_diff(to_date, from_date) < 0:
			frappe.throw(_("To Date cannot be before From Date."))


	def get_columns(self):
		self.columns = [{
				"label": _("Name"),
				"fieldname": "entity",
				"fieldtype": "Data",
				"width":  250
			}]

		for end_date in self.periodic_daterange:
			period = self.get_period(end_date[1])
			self.columns.append({
				"label": _(period),
				"fieldname": scrub(period),
				"fieldtype": "Float",
				"width": 120
			})

		self.columns.append({
			"label": _("Total"),
			"fieldname": "total",
			"fieldtype": "Float",
			"width": 120
		})

	def get_data(self):
		self.get_sales_transactions_based_on_items()
		self.get_rows()

	def get_conditions_sales(self):
		conditions = ''
		if self.filters.brand:
			conditions += "and wb_sas.brand_name = %s" %frappe.db.escape(self.filters.brand)

		if self.filters.subject:
			conditions += "and wb_sas.subject_name = %s" %frappe.db.escape(self.filters.subject)

		return conditions

	def get_conditions_stock(self):
		conditions = ''
		if self.filters.brand:
			conditions += "and wb_stock.brand = %s" %frappe.db.escape(self.filters.brand)

		if self.filters.subject:
			conditions += "and wb_stock.subject = %s" %frappe.db.escape(self.filters.subject)

		return conditions

	def get_sales_transactions_based_on_items(self):

		conditions_sales = self.get_conditions_sales()
		conditions_stock = self.get_conditions_stock()
		warehouse = "%s" %frappe.db.escape(self.filters.warehouse)
		company = "%s" %frappe.db.escape(self.filters.company)
		customer = "%s" %frappe.db.escape(self.filters.customer)

		all_entries = []
		for date in self.periodic_daterange:
			from_date = "'%s'" %date[0]
			to_date = "'%s'" %date[1]

			entries_sales = frappe.db.sql("""
				select IFNULL(sum(wb_sas.retail_price_withdisc_rub), 0) as sales_amount, 
				IFNULL(sum(wb_sas.retail_commission), 0) as amount_commission_wb
				from `tabWB Sales by Sales` wb_sas
				where wb_sas.supplier_oper_name = "Продажа" and wb_sas.sale_dt between {1} and {2} {0}
			"""
			.format(conditions_sales, from_date, to_date), as_dict=1)

			supplier_remuneration = frappe.db.sql("""
				select IFNULL(sum(wb_sas.for_pay), 0) as supplier_remuneration
				from `tabWB Sales by Sales` wb_sas
				where wb_sas.supplier_oper_name = "Продажа" and wb_sas.sale_dt between {1} and {2} {0}
			"""
			.format(conditions_sales, from_date, to_date), as_dict=1)

			total_qty = frappe.db.sql("""
				select IFNULL(sum(wb_sas.quantity), 0) total_qty
				from `tabWB Sales by Sales` wb_sas
				where wb_sas.supplier_oper_name = "Продажа" and wb_sas.sale_dt between {1} and {2} {0}
			"""
			.format(conditions_sales, from_date, to_date), as_dict=1)

			logistics = frappe.db.sql("""
				select IFNULL(sum(wb_sas.delivery_rub), 0) as amount_logistics
				from `tabWB Sales by Sales` wb_sas
				where wb_sas.supplier_oper_name = "Логистика" and wb_sas.sale_dt between {1} and {2} {0}
			"""
			.format(conditions_sales, from_date, to_date), as_dict=1)

			purchases = frappe.db.sql("""
				select sum((select IFNULL(avg(sle.valuation_rate), 0)
					from `tabStock Ledger Entry` sle
					where sle.item_code = (select parent from `tabItem Barcode` where barcode = wb_sas.barcode)
					and sle.creation between {2} and {3}
					and sle.modified between {2} and {3} 
					and sle.warehouse = {0} and sle.company = {1})) amount_purchases
				from `tabWB Sales by Sales` wb_sas
				where wb_sas.supplier_oper_name = "Продажа" and wb_sas.sale_dt between {2} and {3} {4}
			"""
			.format(warehouse, company, from_date, to_date, conditions_sales), as_dict=1)

			if purchases[0]["amount_purchases"] == None:
				purchases[0]["amount_purchases"] = 0.0

			if self.filters.warehouse_storage:
				storage = frappe.db.sql("""
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
					select IFNULL(sum(wb_stock.cost_storage), 0) as stock_balance
					from `tabWB Stocks` wb_stock
					where wb_stock.last_change_date = {0} {1}
				"""
				.format(from_date, conditions_stock), as_dict=1)

				storage = [{"cost_storage": stock_balance[0]['stock_balance']}]

			city_name = {"Коледино": "koledino", "Подольск": "podolsk", "Пушкино": "pushkino", "Электросталь": "elektrostal", 
				"Домодедово": "domodedovo", "Краснодар": "krasnodar", "Екатеринбург": "yekaterinburg", "Хабаровск": "khabarovsk", 
					"Санкт-Петербург": "piter", "Казань": "kazan","Новосибирск": "novosibirsk"}

			all_city = []
			for key, value in iteritems(city_name):
				city = "%s" %frappe.db.escape(key)
				city_qty = frappe.db.sql("""
					select sum(wb_sas.quantity) {4}
					from `tabWB Sales by Sales` wb_sas
					where wb_sas.supplier_oper_name = "Продажа" and wb_sas.office_name = {3} and wb_sas.sale_dt between {1} and {2} {0}
				"""
				.format(conditions_sales, from_date, to_date, city, value), as_dict=1)

				all_city.extend(city_qty)

			calculated_supplier_remuneration = (entries_sales[0]['sales_amount'] - entries_sales[0]['amount_commission_wb'] 
				- logistics[0]['amount_logistics'] - storage[0]['cost_storage'])
			calculated_supplier_remuneration = {"calculated_supplier_remuneration": calculated_supplier_remuneration}

			net_profit = supplier_remuneration[0]['supplier_remuneration'] - purchases[0]['amount_purchases']
			net_profit_percent = (net_profit / entries_sales[0]['sales_amount']) if entries_sales[0]['sales_amount'] else net_profit
			net_profit = {"net_profit": net_profit}
			net_profit_percent = {"net_profit_percent": net_profit_percent}
			calculated_net_profit = (calculated_supplier_remuneration["calculated_supplier_remuneration"] 
				- purchases[0]['amount_purchases'])
			calculated_net_profit_percent = ((calculated_net_profit / entries_sales[0]['sales_amount']) 
				if entries_sales[0]['sales_amount'] else calculated_net_profit)
			calculated_net_profit_percent = {"calculated_net_profit_percent": calculated_net_profit_percent}
			calculated_net_profit = {"calculated_net_profit": calculated_net_profit}
			minus_commission = entries_sales[0]['sales_amount'] - entries_sales[0]['amount_commission_wb']
			commission_percent_wb = (((entries_sales[0]['sales_amount'] - minus_commission) / entries_sales[0]['sales_amount']) 
				if entries_sales[0]['sales_amount'] else (entries_sales[0]['sales_amount'] - minus_commission))
			commission_percent_wb = {"commission_percent_wb": commission_percent_wb}
			logistics_percent_wb = ((logistics[0]['amount_logistics'] / entries_sales[0]['sales_amount']) 
				if entries_sales[0]['sales_amount'] else logistics[0]['amount_logistics'])
			logistics_percent_wb = {"logistics_percent_wb": logistics_percent_wb}
			storage_percent_wb = ((storage[0]['cost_storage'] / entries_sales[0]['sales_amount']) 
				if entries_sales[0]['sales_amount'] else storage[0]['cost_storage'])
			storage_percent_wb = {"storage_percent_wb": storage_percent_wb}
			purchase_percent = ((purchases[0]['amount_purchases'] / entries_sales[0]['sales_amount']) 
				if entries_sales[0]['sales_amount'] else purchases[0]['amount_purchases'])
			purchase_percent = {"purchase_percent": purchase_percent}

			entries = {}
			entries.update(entries_sales[0])
			entries.update(commission_percent_wb)
			entries.update(logistics[0])
			entries.update(logistics_percent_wb)
			entries.update(storage[0])
			entries.update(storage_percent_wb)
			entries.update(supplier_remuneration[0])
			entries.update(calculated_supplier_remuneration)
			entries.update(purchases[0])
			entries.update(purchase_percent)
			entries.update(net_profit)
			entries.update(net_profit_percent)
			entries.update(calculated_net_profit)
			entries.update(calculated_net_profit_percent)
			entries.update(total_qty[0])
			for i in all_city:
				entries.update(i)
			entries.update({"from_date": date[0]})

			all_entries.append(entries)

		self.entries = all_entries

	def get_rows(self):
		self.data = []
		self.get_periodic_data()

		string_name = {"sales_amount": _("Sales amount"), "amount_commission_wb": _("Amount commission WB"), 
				"amount_logistics": _("Minus logistics"), "cost_storage": _("Minus storage in the warehouse"),
				"supplier_remuneration": _("Remuneration to the supplier on the report"), 
				"calculated_supplier_remuneration": _("Calculated remuneration to the supplier"), "amount_purchases": _("Amount purchases"), 
				"net_profit": _("Net profit on the report"), "calculated_net_profit": _("Calculated net profit"),
				"total_qty": _("Total qty"), "koledino": _("Koledino Warehouse"), "podolsk": _("Podolsk Warehouse"), 
				"piter": _("Saint-Petersburg Warehouse"), "kazan": _("Kazan Warehouse"), "yekaterinburg": _("Yekaterinburg Warehouse"),
				"novosibirsk": _("Novosibirsk Warehouse"), "krasnodar": _("Krasnodar Warehouse"), "pushkino": _("Pushkino Warehouse"),
				"elektrostal": _("Elektrostal Warehouse"), "domodedovo": _("Domodedovo Warehouse"), "khabarovsk": _("Khabarovsk Warehouse"),
				"commission_percent_wb": _("Commission percent wb"), "logistics_percent_wb": _("Logistics percent"), 
				"storage_percent_wb": _("Storage percent"), "purchase_percent": _("Purchase percent"), 
				"net_profit_percent": _("Net profit percent"), "calculated_net_profit_percent": _("Calculated net profit percent"),}

		for entity, period_data in iteritems(self.entity_periodic_data):
			if entity == 'from_date':
				continue

			row = {
				"entity": string_name[entity]
			}
			total = 0
			for date in self.periodic_daterange:
				period = self.get_period(date[1])
				amount = flt(period_data.get(period, 0.0))
				row[scrub(period)] = amount
				total += amount

			row["total"] = total

			self.data.append(row)

	def get_periodic_data(self):
		self.entity_periodic_data = frappe._dict()

		for d in self.entries:
			for key, value in d.items():
				period = self.get_period(d["from_date"])
				self.entity_periodic_data.setdefault(key, frappe._dict()).setdefault(period, 0.0)
				self.entity_periodic_data[key][period] += flt(value)

	def get_period(self, posting_date):
		if self.filters.range == 'Weekly':
			period = "Week " + str(posting_date.isocalendar()[1]) + " " + str(posting_date.year)
		elif self.filters.range == 'Monthly':
			period = str(self.months[posting_date.month - 1]) + " " + str(posting_date.year)
		elif self.filters.range == 'Quarterly':
			period = "Quarter " + str(((posting_date.month - 1) // 3) + 1) + " " + str(posting_date.year)
		else:
			year = get_fiscal_year(posting_date, company=self.filters.company)
			period = str(year[0])
		return period

	def get_period_date_ranges(self):
		from dateutil.relativedelta import relativedelta, MO
		from_date, to_date = getdate(self.filters.from_date), getdate(self.filters.to_date)

		increment = {
			"Monthly": 1,
			"Quarterly": 3,
			"Half-Yearly": 6,
			"Yearly": 12
		}.get(self.filters.range, 1)

		if self.filters.range in ['Monthly', 'Quarterly']:
			from_date = from_date.replace(day=1)
		elif self.filters.range == "Yearly":
			from_date = get_fiscal_year(from_date)[1]
		else:
			from_date = from_date + relativedelta(from_date, weekday=MO(-1))

		self.periodic_daterange = []
		for dummy in range(1, 53):
			if self.filters.range == "Weekly":
				period_end_date = add_days(from_date, 6)
			else:
				period_end_date = add_to_date(from_date, months=increment, days=-1)

			if period_end_date > to_date:
				period_end_date = to_date

			self.periodic_daterange.append((from_date, period_end_date))

			from_date = add_days(period_end_date, 1)
			if period_end_date == to_date:
				break

	def get_chart_data(self):
		length = len(self.columns)

		if self.filters.tree_type in ["Customer", "Supplier"]:
			labels = [d.get("label") for d in self.columns[2:length - 1]]
		elif self.filters.tree_type == "Item":
			labels = [d.get("label") for d in self.columns[3:length - 1]]
		else:
			labels = [d.get("label") for d in self.columns[1:length - 1]]
		self.chart = {
			"data": {
				'labels': labels,
				'datasets': []
			},
			"type": "line"
		}
