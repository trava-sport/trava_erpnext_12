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
		self.filters = frappe._dict(filters or {})
		self.validate_filters()
		self.date_field = 'transaction_date' \
			if self.filters.doc_type in ['Sales Order', 'Purchase Order'] else 'posting_date'
		self.months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
		self.get_period_date_ranges()

	def run(self):
		self.get_columns()
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
				"label": _("Supplier's article number"),
				"fieldname": "entity",
				"fieldtype": "Data",
				"width":  170
			}]

		self.columns.append({
				"label": _("Size"),
				"fieldname": "size",
				"fieldtype": "Data",
				"width":  80
			})

		self.columns.append({
				"label": _("Barcode"),
				"fieldname": "barcode",
				"fieldtype": "Data",
				"width":  130
			})

		self.columns.append({
				"label": _("WB article number"),
				"fieldname": "wb_article_number",
				"fieldtype": "Data",
				"width":  100
			})

		for end_date in self.periodic_daterange:
			period = self.get_period(end_date)
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

		if self.filters.all_subject_except:
			conditions += "and wb_sas.subject_name != %s" %frappe.db.escape(self.filters.all_subject_except)

		return conditions

	def get_sales_transactions_based_on_items(self):

		conditions_sales = self.get_conditions_sales()
		from_date = "'%s'" %self.filters.from_date
		to_date = "'%s'" %self.filters.to_date

		self.entries = frappe.db.sql("""
			select wb_sas.sa_name as entity, wb_sas.ts_name as size, wb_sas.barcode as barcode, 
			wb_sas.nm_id as wb_article_number, wb_sas.sale_dt as sale_date, wb_sas.supplier_oper_name,
			ifnull(sum(wb_sas.quantity), 0) as quantity
			from `tabWB Sales by Sales` wb_sas
			where (wb_sas.supplier_oper_name = "Продажа" or wb_sas.supplier_oper_name = "Возврат")
			and wb_sas.sale_dt between {1} and {2} {0}
			group by wb_sas.sa_name, wb_sas.ts_name, wb_sas.sale_dt
		"""
		.format(conditions_sales, from_date, to_date), as_dict=1)

		self.entity_names = {}
		for d in self.entries:
			self.entity_names.setdefault(d.entity, [d.size, d.barcode, d.wb_article_number])

	def get_rows(self):
		self.data = []
		self.get_periodic_data()

		for entity, period_data in iteritems(self.entity_periodic_data):
			row = {
				"entity": entity,
				"size": self.entity_names.get(entity)[0],
				"barcode": self.entity_names.get(entity)[1],
				"wb_article_number": self.entity_names.get(entity)[2]
			}
			total = 0
			for end_date in self.periodic_daterange:
				period = self.get_period(end_date)
				amount = flt(period_data.get(period, 0.0))
				row[scrub(period)] = amount
				total += amount

			row["total"] = total

			self.data.append(row)

	def get_periodic_data(self):
		self.entity_periodic_data = frappe._dict()

		for d in self.entries:
			period = self.get_period(d.sale_date)
			self.entity_periodic_data.setdefault(d.entity, frappe._dict()).setdefault(period, 0.0)
			if d.supplier_oper_name == "Продажа":
				self.entity_periodic_data[d.entity][period] += flt(d.quantity)
			else:
				self.entity_periodic_data[d.entity][period] -= flt(d.quantity)

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

			self.periodic_daterange.append(period_end_date)

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
