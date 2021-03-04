# -*- coding: utf-8 -*-
# Copyright (c) 2020, trava and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import dateutil
from datetime import timedelta, datetime
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from erpnext.erpnext_integrations.doctype.amazon_mws_settings.amazon_methods import get_orders
from trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods import get_report
from trava_erpnext.sale_commission.doctype.commission_agent_report.commission_agent_report import create_report_commission_from_wb_sbs

class WBSettings(Document):
	def validate(self):
		if self.enable_wb == 1:
			self.enable_sync = 1
			#setup_custom_fields()
		else:
			self.enable_sync = 0

	def get_products_details(self):
		if self.enable_wb == 1:
			frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_methods.get_products_details')

	def get_order_details(self):
		if self.enable_wb == 1:
			after_date = dateutil.parser.parse(self.after_date).strftime("%Y-%m-%d")
			frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_methods.get_orders', after_date=after_date)

	def get_report_stocks(self):
		if self.enable_wb == 1:
			dateFrom = datetime.today().date()
			frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report', dateFrom=dateFrom, 
				reportType='stocks', doc='WB Stocks')

	def get_report_orders(self):
		if not self.date_from_orders:
			frappe.throw(_("You must specify the date from."))
		if self.enable_wb == 1:
			dateFrom = self.date_from_orders
			frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report', dateFrom=dateFrom, 
				reportType='orders', doc='WB Orders', flag=1, timeout=4500)

	def get_report_sales(self):
		if not self.date_from_sales:
			frappe.throw(_("You must specify the date from."))
		if self.enable_wb == 1:
			dateFrom = self.date_from_sales
			frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report', dateFrom=dateFrom, 
				reportType='sales', doc='WB Sales', flag=1, timeout=4500)

	def get_report_sales_by_sales(self):
		if not self.date_from or not self.date_to:
			frappe.throw(_("You must specify the date from and to."))
		if self.enable_wb == 1:
			dateFrom = self.date_from
			dateTo = self.date_to
			frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report', dateFrom=dateFrom, 
				dateTo=dateTo, reportType='reportDetailByPeriod', doc='WB Sales by Sales Monthly', timeout=4500)

	def create_commission_agent_report(self):
		if not self.date_from_sbs or not self.date_to_sbs:
			frappe.throw(_("You must specify the date from and to."))
		dateFrom = datetime.strptime(self.date_from_sbs, '%Y-%m-%d')
		dateTo = datetime.strptime(self.date_to_sbs, '%Y-%m-%d')
		create_report_commission_from_wb_sbs(dateFrom, dateTo)

def schedule_get_order_details():
	mws_settings = frappe.get_doc("WB Settings")
	if mws_settings.enable_sync and mws_settings.enable_wb:
		after_date = dateutil.parser.parse(mws_settings.after_date).strftime("%Y-%m-%d")
		get_orders(after_date = after_date)

@frappe.whitelist()
def schedule_get_report_stocks():
	mws_settings = frappe.get_doc("WB Settings")
	if mws_settings.enable_sync and mws_settings.enable_wb:
		dateFrom = datetime.today().date()
		frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report', dateFrom=dateFrom, 
			reportType='stocks', doc='WB Stocks', timeout=4500)

@frappe.whitelist()
def schedule_get_report_orders_daily():
	mws_settings = frappe.get_doc("WB Settings")
	if mws_settings.enable_sync and mws_settings.enable_wb:
		now = datetime.today()
		today = datetime.today().date()
		today23am = now.replace(hour=0, minute=25, second=0, microsecond=0)
		if now < today23am:
			dateFrom = today - timedelta(days=1)
		dateFrom = today
		frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report', dateFrom=dateFrom, 
			reportType='orders', doc='WB Orders', flag=1, timeout=4500)

@frappe.whitelist()
def schedule_get_report_orders_monthly():
	mws_settings = frappe.get_doc("WB Settings")
	if mws_settings.enable_sync and mws_settings.enable_wb:
		now = datetime.now()
		thirty_five_days = timedelta(days=35)
		dateFrom = now - thirty_five_days
		frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report', dateFrom=dateFrom, 
			reportType='orders', doc='WB Orders', flag=1, monthly=True, timeout=4500)

@frappe.whitelist()
def schedule_get_report_sales_daily():
	mws_settings = frappe.get_doc("WB Settings")
	if mws_settings.enable_sync and mws_settings.enable_wb:
		now = datetime.today()
		today = datetime.today().date()
		today23am = now.replace(hour=0, minute=25, second=0, microsecond=0)
		if now < today23am:
			dateFrom = today - timedelta(days=1)
		dateFrom = today
		frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report', dateFrom=dateFrom, 
			reportType='sales', doc='WB Sales', flag=1, timeout=4500)

@frappe.whitelist()
def schedule_get_report_sales_monthly():
	mws_settings = frappe.get_doc("WB Settings")
	if mws_settings.enable_sync and mws_settings.enable_wb:
		now = datetime.now()
		thirty_five_days = timedelta(days=35)
		dateFrom = now - thirty_five_days
		frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report', dateFrom=dateFrom, 
			reportType='sales', doc='WB Sales', flag=1, monthly=True, timeout=4500)

@frappe.whitelist()
def schedule_get_report_sales_by_sales():
	mws_settings = frappe.get_doc("WB Settings")
	if mws_settings.enable_sync and mws_settings.enable_wb:
		now = datetime.now()
		eight_days = timedelta(days=8)
		two_days = timedelta(days=2)
		dateFrom = now - eight_days
		dateTo = now - two_days
		frappe.enqueue('trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report', dateFrom=dateFrom, 
			dateTo=dateTo, reportType='reportDetailByPeriod', doc='WB Sales by Sales', timeout=4500)

def setup_custom_fields():
	custom_fields = {
		"Item": [dict(fieldname='amazon_item_code', label='Amazon Item Code',
			fieldtype='Data', insert_after='series', read_only=1, print_hide=1)],
		"Sales Order": [dict(fieldname='amazon_order_id', label='Amazon Order ID',
			fieldtype='Data', insert_after='title', read_only=1, print_hide=1)]
	}

	create_custom_fields(custom_fields)
