# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, time, dateutil, math, csv
from six import StringIO
import trava_erpnext.trava_integrations.doctype.wb_settings.wb_api as mws
from frappe import _

from datetime import datetime, timedelta

# Синхронизация по отчету Stocks запускается три раза в день. Данные из этого отчета не удаляются.

# Синхронизация по отчетам Orders и Sales запускается каждые 30 минут с параметром по умолчанию flag=0. 
# При этом данные из него не удаляются. Также синхронизация по отчету Orders запускается каждый
# месяц 4 чмсла с параметром по умолчанию flag=1 и датой равной -35 дней от текущей датой. Перед
# этим удалив данные за этот же период. С параметром по умолчанию flag=0 количество возвращенных 
# строк данных варьируется в интервале от 0 до примерно 100000.

# Синхронизация по отчету Sales_by_sales запускается каждый вторник с параметрами dateFrom равным
# минус восемь дней от текущей даты и dateTo равным минус два дня от текущей даты. Данные при
# этом не удаляэтся.

# Есть отчет Sales_by_sales заполняющей таблицу WB Sales by Sales Monthly и запускающийся по кнопке.
# Данный отчет перед этим удаляет все

#Get and Create Products
@frappe.whitelist()
def get_report(dateFrom, reportType, doc, dateTo=None, flag=0, monthly=False, rrd_id=0):
	frappe.logger("my").info('reportType {0}, dateFrom {1}'.format(reportType, dateFrom))
	if flag == 1 and monthly == True:
		create_report(dateFrom, reportType, doc, flag)
	else:
		reports = get_reports_instance()

		report_response = call_mws_method(reports.get_report,reportType=reportType,
			dateFrom=dateFrom, dateTo=dateTo, flag=flag, rrd_id=rrd_id)

		if reportType == 'stocks':
			deleting_data_in_wb_report(dateFrom, reportType, doc)
			create_report_stocks(report_response)
		elif reportType == 'orders':
			deleting_data_in_wb_report(dateFrom, reportType, doc)
			create_report_orders(report_response)
		elif reportType == 'sales':
			deleting_data_in_wb_report(dateFrom, reportType, doc)
			create_report_sales(report_response)
		elif reportType == 'reportDetailByPeriod':
			if doc == 'WB Sales by Sales Monthly':
				deleting_data_in_wb_report(dateFrom, reportType, doc)
			create_report_sales_by_sales(report_response, dateFrom, dateTo, reportType, doc, rrd_id)

def get_reports_instance():
	mws_settings = frappe.get_doc("WB Settings")
	reports = mws.WBReports(
			account_id = mws_settings.seller_id,
			access_key = mws_settings.aws_access_key_id,
			secret_key = mws_settings.secret_key,
			region = mws_settings.region,
			domain = mws_settings.domain
	)

	return reports

def call_mws_method(mws_method, *args, **kwargs):

	mws_settings = frappe.get_doc("WB Settings")
	max_retries = mws_settings.max_retry_limit

	for x in range(0, max_retries):
		try:
			response = mws_method(*args, **kwargs)
			return response
		except Exception as e:
			delay = math.pow(4, x) * 60
			method = str(mws_method)
			method = method[:-27]
			frappe.log_error(message=e, title=method)
			frappe.logger("my").info('fgh {0}'.format(delay))
			time.sleep(delay)
			continue

	mws_settings.enable_sync = 0
	mws_settings.save()

	frappe.throw(_("Sync has been temporarily disabled because maximum retries have been exceeded"))

def deleting_data_in_wb_report(dateFrom, reportType, doc):
	if reportType in ('stocks', 'orders','sales'):
		frappe.db.sql('''delete from `tab{0}` where `last_change_date`="%s"''' # nosec
			.format(doc) % (dateFrom))

	elif reportType in ('reportDetailByPeriod'):
		frappe.db.sql("""delete from `tabWB Sales by Sales Monthly`""")

def create_report(dateFrom, reportType, doc, flag):
	update_date = datetime.strptime(dateFrom, "%Y-%m-%d").date()
	date_today = datetime.today().date()
	while update_date != date_today:
		frappe.logger("my").info('fgh {0}'.format(update_date))
		frappe.logger("my").info('fgh {0}'.format(date_today))
		reports = get_reports_instance()

		report_response = call_mws_method(reports.get_report,reportType=reportType,
			dateFrom=update_date, flag=flag)
		
		if reportType == 'orders':
			deleting_data_in_wb_report(update_date, reportType, doc)
			create_report_orders(report_response)
		elif reportType == 'sales':
			deleting_data_in_wb_report(update_date, reportType, doc)
			create_report_sales(report_response)

		update_date += timedelta(days=1)

def create_report_stocks(report_response):
	for data in report_response:
		cost_storage = frappe.db.get_value("WB Deductions", 
			filters={"subject":data['subject']}, fieldname="cost_storage")
		if cost_storage == None:
			cost_storage = 0.03
		calculate_cost_storage = data['quantityFull'] * cost_storage
		item = frappe.new_doc("WB Stocks")

		item.last_change_date = data['lastChangeDate']
		item.last_change_date_and_time = datetime.strptime(data['lastChangeDate'], "%Y-%m-%dT%H:%M:%S.%f")
		item.supplier_article = data['supplierArticle']
		item.tech_size = data['techSize']
		item.barcode = data['barcode']
		item.quantity = data['quantity']
		item.is_supply = data['isSupply']
		item.is_realization = data['isRealization']
		item.quantity_full = data['quantityFull']
		item.quantity_not_in_orders = data['quantityNotInOrders']
		item.warehouse_name = data['warehouseName']
		item.in_way_to_client = data['inWayToClient']
		item.in_way_from_client = data['inWayFromClient']
		item.nmid = data['nmId']
		item.subject = data['subject']
		item.category = data['category']
		item.days_on_site = data['daysOnSite']
		item.brand = data['brand']
		item.sccode = data['SCCode']
		item.price = data['Price']
		item.discount = data['Discount']
		item.cost_storage = calculate_cost_storage

		item.insert(ignore_permissions=True)

def create_report_orders(report_response):
	for data in report_response:
		item = frappe.new_doc("WB Orders")

		item.number = data['number']
		item.date = datetime.strptime(data['date'], "%Y-%m-%dT%H:%M:%S")
		item.last_change_date = data['lastChangeDate']
		item.last_change_date_and_time = datetime.strptime(data['lastChangeDate'], "%Y-%m-%dT%H:%M:%S")
		item.supplier_article = data['supplierArticle']
		item.tech_size = data['techSize']
		item.barcode = data['barcode']
		item.quantity = data['quantity']
		item.total_price = data['totalPrice']
		item.discount_percent = data['discountPercent']
		item.warehouse_name = data['warehouseName']
		item.oblast = data['oblast']
		item.income_id = data['incomeID']
		item.odid = data['odid']
		item.nmid = data['nmId']
		item.subject = data['subject']
		item.category = data['category']
		item.brand = data['brand']
		item.is_cancel = str(data['isCancel'])
		item.cancel_dt = data['cancel_dt']

		item.insert(ignore_permissions=True)

def create_report_sales(report_response):
	for data in report_response:
		item = frappe.new_doc("WB Sales")

		item.number = data['number']
		item.date = datetime.strptime(data['date'], "%Y-%m-%dT%H:%M:%S")
		item.last_change_date = data['lastChangeDate']
		item.last_change_date_and_time = datetime.strptime(data['lastChangeDate'], "%Y-%m-%dT%H:%M:%S")
		item.supplier_article = data['supplierArticle']
		item.tech_size = data['techSize']
		item.barcode = data['barcode']
		item.quantity = data['quantity']
		item.total_price = data['totalPrice']
		item.discount_percent = data['discountPercent']
		item.is_supply = data['isSupply']
		item.is_realization = data['isRealization']
		item.order_id = data['orderId']
		item.promo_code_discount = data['promoCodeDiscount']
		item.warehouse_name = data['warehouseName']
		item.country_name = data['countryName']
		item.oblast_okrug_name = data['oblastOkrugName']
		item.region_name = data['regionName']
		item.income_id = data['incomeID']
		item.sale_id = data['saleID']
		item.odid = data['odid']
		item.spp = data['spp']
		item.for_pay = data['forPay']
		item.finished_price = data['finishedPrice']
		item.price_with_disc = data['priceWithDisc']
		item.nmid = data['nmId']
		item.subject = data['subject']
		item.category = data['category']
		item.brand = data['brand']
		item.is_storno = data['IsStorno']

		item.insert(ignore_permissions=True)

def create_report_sales_by_sales(report_response, dateFrom, dateTo, reportType, doc, rrd_id):
	while rrd_id != '':
		if rrd_id != 0:
			reports = get_reports_instance()

			report_response = call_mws_method(reports.get_report,reportType=reportType,
				dateFrom=dateFrom, dateTo=dateTo, rrd_id=rrd_id)
			if report_response == []:
				return
			rrd_id = create_report_sbs(report_response, doc)

		rrd_id = create_report_sbs(report_response, doc)

def create_report_sbs(report_response, doc):
	for data in report_response:
		item = frappe.new_doc(doc)

		item.realizationreport_id = data['realizationreport_id']
		item.suppliercontract_code = data['suppliercontract_code']
		item.rr_dt = data['rr_dt']
		item.rr_dt_and_time = datetime.strptime(data['rr_dt'], "%Y-%m-%dT%H:%M:%S")
		item.rrd_id = data['rrd_id']
		item.subject_name = data['subject_name']
		item.nm_id = data['nm_id']
		item.brand_name = data['brand_name']
		item.sa_name = data['sa_name']
		item.ts_name = data['ts_name']
		item.barcode = data['barcode']
		item.doc_type_name = data['doc_type_name']
		item.quantity = data['quantity']
		item.nds = data['nds']
		item.cost_amount = data['cost_amount']
		item.retail_price = data['retail_price']
		item.retail_amount = data['retail_amount']
		item.retail_commission = data['retail_commission']
		item.sale_percent = data['sale_percent']
		item.commission_percent = data['commission_percent']
		item.customer_reward = data['customer_reward']
		item.supplier_reward = data['supplier_reward']
		item.office_name = data['office_name']
		item.supplier_oper_name = data['supplier_oper_name']
		item.order_dt = datetime.strptime(data['order_dt'], "%Y-%m-%dT%H:%M:%S")
		item.sale_dt = datetime.strptime(data['sale_dt'], "%Y-%m-%dT%H:%M:%S")
		item.shk_id = data['shk_id']
		item.retail_price_withdisc_rub = data['retail_price_withdisc_rub']
		item.for_pay = data['for_pay']
		item.for_pay_nds = data['for_pay_nds']
		item.delivery_amount = data['delivery_amount']
		item.return_amount = data['return_amount']
		item.delivery_rub = data['delivery_rub']
		item.gi_box_type_name = data['gi_box_type_name']
		item.product_discount_for_report = data['product_discount_for_report']
		item.supplier_promo = data['supplier_promo']
		item.supplier_spp = data['supplier_spp']

		item.insert(ignore_permissions=True)

	rrd_id = report_response[-1]['rrd_id']
    
	return rrd_id