# -*- coding: utf-8 -*-
# Copyright (c) 2021, trava and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document
from datetime import timedelta, datetime, date

class WBPrice(Document):

	def validate(self):
		self.validate_data_item()
		self.validate_number_sales()
		self.validate_remains()

	def validate_data_item(self):
		try:
			existing_subject_delivery_cost = frappe.db.get_value("WB Deductions", 
				filters={"subject":self.subject}, fieldname="cost")
			existing_subject_remuneration = frappe.db.get_value("WB Deductions", 
				filters={"subject":self.subject}, fieldname="wb_percentage_remuneration")

			assert existing_subject_delivery_cost != None
			assert existing_subject_remuneration != None
		except Exception:
			frappe.throw(_("In the line with the value of the barcode %s, the ""subject"" field is not filled in." % self.last_barcode))

		self.get_valuation_rate()

		if self.changing_promo_code:
			self.new_promo_code_discount = self.current_promo_code_discount + self.changing_promo_code

		if self.new_retail_price:
			if self.desired_net_profit:
				if self.new_promo_code_discount:
					self.agreed_discount = 100 - ((((self.desired_net_profit + (existing_subject_delivery_cost * 2) + self.valuation_rate)
						* 100 / (100 - existing_subject_remuneration)) * 100 / (100 - self.new_promo_code_discount)) 
							* 100 / self.new_retail_price)
				else:
					self.agreed_discount = 100 - ((((self.desired_net_profit + (existing_subject_delivery_cost * 2) + self.valuation_rate)
						* 100 / (100 - existing_subject_remuneration)) * 100 / (100 - self.current_promo_code_discount)) 
							* 100 / self.new_retail_price)

			if self.agreed_discount:
				self.new_price_discount = self.calculation_retail_price_discounts(self.new_retail_price, self.agreed_discount)
			else:
				self.new_price_discount = self.calculation_retail_price_discounts(self.new_retail_price, self.current_discount_site)

			if self.new_promo_code_discount:
				self.new_price_disc_promo_code = self.calculation_retail_price_discounts(self.new_price_discount, self.new_promo_code_discount)
			else:
				self.new_price_disc_promo_code = self.calculation_retail_price_discounts(self.new_price_discount, self.current_promo_code_discount)

			self.new_net_profit = self.calculation_net_profit(self.new_price_disc_promo_code, self.valuation_rate,
				existing_subject_delivery_cost, existing_subject_remuneration)

			#Вычесляем новую розничную цену за вычитом скидки и промо кода и за вычитам дополнительной 10 процентной скидки для акциий
			new_price_disc_promo_code = self.calculation_retail_price_discounts(self.new_price_disc_promo_code, 10)

			self.new_net_profit_discount = self.calculation_net_profit(new_price_disc_promo_code, self.valuation_rate,
				existing_subject_delivery_cost, existing_subject_remuneration)

		else:
			if self.desired_net_profit:
				if self.new_promo_code_discount:
					self.agreed_discount = 100 - ((((self.desired_net_profit + (existing_subject_delivery_cost * 2) + self.valuation_rate)
						* 100 / (100 - existing_subject_remuneration)) * 100 / (100 - self.new_promo_code_discount)) 
							* 100 / self.current_retail_price)
				else:
					self.agreed_discount = 100 - ((((self.desired_net_profit + (existing_subject_delivery_cost * 2) + self.valuation_rate)
						* 100 / (100 - existing_subject_remuneration)) * 100 / (100 - self.current_promo_code_discount)) 
							* 100 / self.current_retail_price)

			if self.agreed_discount or self.new_promo_code_discount:
				if self.agreed_discount:
					self.new_price_discount = self.calculation_retail_price_discounts(self.current_retail_price, self.agreed_discount)
				else:
					self.new_price_discount = self.calculation_retail_price_discounts(self.current_retail_price, self.current_discount_site)

				if self.new_promo_code_discount:
					self.new_price_disc_promo_code = self.calculation_retail_price_discounts(self.new_price_discount, self.new_promo_code_discount)
				else:
					self.new_price_disc_promo_code = self.calculation_retail_price_discounts(self.new_price_discount, self.current_promo_code_discount)

				self.new_net_profit = self.calculation_net_profit(self.new_price_disc_promo_code, self.valuation_rate,
					existing_subject_delivery_cost, existing_subject_remuneration)

				#Вычесляем новую розничную цену за вычитом скидки и промо кода и за вычитам дополнительной 10 процентной скидки для акциий
				new_price_disc_promo_code = self.calculation_retail_price_discounts(self.new_price_disc_promo_code, 10)

				self.new_net_profit_discount = self.calculation_net_profit(new_price_disc_promo_code, self.valuation_rate,
					existing_subject_delivery_cost, existing_subject_remuneration)

		self.current_price_discount = self.calculation_retail_price_discounts(self.current_retail_price, self.current_discount_site)
		self.current_price_disc_promo_code = self.calculation_retail_price_discounts(self.current_price_discount, self.current_promo_code_discount)
		self.current_net_profit = self.calculation_net_profit(self.current_price_disc_promo_code, 
			self.valuation_rate, existing_subject_delivery_cost, existing_subject_remuneration)

	def get_valuation_rate(self):
		barcode = "%s" %frappe.db.escape(self.last_barcode)

		valuation_rate = frappe.db.sql("""
			SELECT IFNULL(sle.valuation_rate, 0) valuation_rate
			FROM `tabStock Ledger Entry` sle
			WHERE sle.item_code = (select parent from `tabItem Barcode` where barcode = {0})
				AND warehouse = 'Готовая продукция - ДС Елены Марьиной'
			order by posting_date desc, posting_time desc, name desc limit 1
		""".format(barcode), as_dict=1)

		if not valuation_rate:
			self.valuation_rate = 0
		else:
			self.valuation_rate = flt(valuation_rate[0]['valuation_rate'])

	def calculation_retail_price_discounts(self, price, discount):
		calculated_price = price - (price * (discount / 100))

		return calculated_price

	def calculation_net_profit(self, price, standard_price, existing_subject_delivery_cost, existing_subject_remuneration):
		net_profit = price - (price * (existing_subject_remuneration / 100)) - standard_price - (existing_subject_delivery_cost * 2)

		return net_profit

	def get_conditions_wb_sales(self):
		to_date_sales = date.today()
		thirty_one_days = timedelta(days=31)
		from_date_sales = to_date_sales - thirty_one_days
		conditions = ''
		conditions += "AND wb_sales.date >= '%s'" %from_date_sales
		conditions += "AND wb_sales.date <= '%s'" %to_date_sales

		return conditions

	def get_conditions_wb_stocks(self):
		date_stock = date.today()
		conditions = "AND wb_stocks.last_change_date = '%s'" %date_stock

		return conditions

	def validate_number_sales(self):
		conditions_wb_sales = self.get_conditions_wb_sales()
		supplier_article = "%s" %frappe.db.escape(self.supplier_article)

		number_of_sales = frappe.db.sql("""
			SELECT IFNULL(SUM(wb_sales.quantity), 0) wb_sales_qty
			FROM `tabWB Sales` wb_sales
			WHERE wb_sales.supplier_article = {0} {1}
		""".format(supplier_article, conditions_wb_sales), as_dict=1)

		if not number_of_sales:
			self.number_of_sales = 0
		else:
			self.number_of_sales = number_of_sales[0]['wb_sales_qty']

	def validate_remains(self):
		conditions_wb_stocks = self.get_conditions_wb_stocks()
		supplier_article = "%s" %frappe.db.escape(self.supplier_article)

		remains = frappe.db.sql("""
			SELECT IFNULL(SUM(wb_stocks.quantity), 0) wb_stocks_qty
			FROM `tabWB Stocks` wb_stocks
			WHERE wb_stocks.supplier_article = {0} {1}
		""".format(supplier_article, conditions_wb_stocks), as_dict=1)

		if not remains:
			self.remains = 0
		else:
			self.remains = remains[0]['wb_stocks_qty']
