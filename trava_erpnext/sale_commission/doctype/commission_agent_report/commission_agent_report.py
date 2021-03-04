# -*- coding: utf-8 -*-
# Copyright (c) 2020, trava and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import sys
import json
from datetime import timedelta, datetime, date
from frappe.model.document import Document
import frappe
from frappe import _, scrub
from frappe.utils import cstr, flt, getdate, cint, nowdate, add_days, get_link_to_form, strip_html
from frappe.model.utils import get_fetch_values
from frappe.model.mapper import get_mapped_doc
from frappe.desk.notifications import clear_doctype_notifications
from frappe.contacts.doctype.address.address import get_company_address
from erpnext.controllers.selling_controller import SellingController
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.accounts.doctype.sales_invoice.sales_invoice import validate_inter_company_party, update_linked_doc,\
	unlink_inter_company_doc
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account
from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account

class CommissionAgentReport(SellingController):

	def validate(self):
		self.validate_proj_cust()
		self.validate_for_items()
		validate_inter_company_party(self.doctype, self.customer, self.company, self.inter_company_order_reference)

		self.validate_with_previous_doc()
		self.set_status()

		if not self.billing_status: self.billing_status = 'Not Billed'

	def validate_proj_cust(self):
		if self.project and self.customer_name:
			res = frappe.db.sql("""select name from `tabProject` where name = %s
				and (customer = %s or ifnull(customer,'')='')""",
					(self.project, self.customer))
			if not res:
				frappe.throw(_("Customer {0} does not belong to project {1}").format(self.customer, self.project))

	def validate_for_items(self):
		for d in self.get('items'):

			tot_avail_qty = frappe.db.sql("select projected_qty from `tabBin` \
				where item_code = %s and warehouse = %s", (d.item_code, d.warehouse))
			d.projected_qty = tot_avail_qty and flt(tot_avail_qty[0][0]) or 0

	def validate_with_previous_doc(self):
		super(CommissionAgentReport, self).validate_with_previous_doc({
			"Quotation": {
				"ref_dn_field": "prevdoc_docname",
				"compare_fields": [["company", "="]]
			}
		})

	def update_enquiry_status(self, prevdoc, flag):
		enq = frappe.db.sql("select t2.prevdoc_docname from `tabQuotation` t1, `tabQuotation Item` t2 where t2.parent = t1.name and t1.name=%s", prevdoc)
		if enq:
			frappe.db.sql("update `tabOpportunity` set status = %s where name=%s",(flag,enq[0][0]))

	def on_submit(self):
		frappe.get_doc('Authorization Control').validate_approving_authority(self.doctype, self.company, self.base_grand_total, self)
		self.update_project()

		update_linked_doc(self.doctype, self.name, self.inter_company_order_reference)

	def on_cancel(self):
		super(CommissionAgentReport, self).on_cancel()

		# Cannot cancel closed SO
		if self.status == 'Closed':
			frappe.throw(_("Closed order cannot be cancelled. Unclose to cancel."))

		self.check_nextdoc_docstatus()
		self.update_project()

		frappe.db.set(self, 'status', 'Cancelled')

		unlink_inter_company_doc(self.doctype, self.name, self.inter_company_order_reference)

	def update_project(self):
		if self.project:
			project = frappe.get_doc("Project", self.project)
			project.update_sales_amount()
			project.db_update()

	def check_nextdoc_docstatus(self):
		# Checks Sales Invoice
		submit_rv = frappe.db.sql_list("""select t1.name
			from `tabSales Invoice` t1,`tabSales Invoice Item` t2
			where t1.name = t2.parent and t2.commission_agent_report = %s and t1.docstatus = 1""",
			self.name)

		if submit_rv:
			submit_rv = [get_link_to_form("Sales Invoice", si) for si in submit_rv]
			frappe.throw(_("Sales Invoice {0} must be cancelled before cancelling this Commission Agent Report")
				.format(", ".join(submit_rv)))

	def check_modified_date(self):
		mod_db = frappe.db.get_value("CommissionAgentReport", self.name, "modified")
		date_diff = frappe.db.sql("select TIMEDIFF('%s', '%s')" %
			( mod_db, cstr(self.modified)))
		if date_diff and date_diff[0][0]:
			frappe.throw(_("{0} {1} has been modified. Please refresh.").format(self.doctype, self.name))

	def update_status(self, status):
		self.check_modified_date()
		self.set_status(update=True, status=status)
		self.notify_update()
		clear_doctype_notifications(self)

	def on_update(self):
		pass

	def set_indicator(self):
		"""Set indicator for portal"""
		if self.per_billed < 100:
			self.indicator_color = "orange"
			self.indicator_title = _("Not Paid")

		else:
			self.indicator_color = "green"
			self.indicator_title = _("Paid")

def get_list_context(context=None):
	from erpnext.controllers.website_list_for_contact import get_list_context
	list_context = get_list_context(context)
	list_context.update({
		'show_sidebar': True,
		'show_search': True,
		'no_breadcrumbs': True,
		'title': _('Orders'),
	})

	return list_context

@frappe.whitelist()
def close_or_unclose_sales_orders(names, status):
	if not frappe.has_permission("Commission Agent Report", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	names = json.loads(names)
	for name in names:
		so = frappe.get_doc("Commission Agent Report", name)
		if so.docstatus == 1:
			if status == "Closed":
				if so.status not in ("Cancelled", "Closed") and (so.per_delivered < 100 or so.per_billed < 100):
					so.update_status(status)
			else:
				if so.status == "Closed":
					so.update_status('Draft')
			so.update_blanket_order()

	frappe.local.message_log = []

@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None, ignore_permissions=False):
	def postprocess(source, target):
		set_missing_values(source, target)
		#Get the advance paid Journal Entries in Sales Invoice Advance
		if target.get("allocate_advances_automatically"):
			target.set_advances()

	def set_missing_values(source, target):
		target.ignore_pricing_rule = 1
		target.flags.ignore_permissions = True
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")

		if source.company_address:
			target.update({'company_address': source.company_address})
		else:
			# set company address
			target.update(get_company_address(target.company))

		if target.company_address:
			target.update(get_fetch_values("Sales Invoice", 'company_address', target.company_address))

	def update_item(source, target, source_parent):
		target.amount = flt(source.amount) - flt(source.billed_amt)
		target.base_amount = target.amount * flt(source_parent.conversion_rate)
		target.qty = target.amount / flt(source.rate) if (source.rate and source.billed_amt) else source.qty - source.returned_qty
		target.award = source.award
		target.base_award = source.base_award

		if source_parent.project:
			target.cost_center = frappe.db.get_value("Project", source_parent.project, "cost_center")
		if target.item_code:
			item = get_item_defaults(target.item_code, source_parent.company)
			item_group = get_item_group_defaults(target.item_code, source_parent.company)
			cost_center = item.get("selling_cost_center") \
				or item_group.get("selling_cost_center")

			if cost_center:
				target.cost_center = cost_center

	doclist = get_mapped_doc("Commission Agent Report", source_name, {
		"Commission Agent Report": {
			"doctype": "Sales Invoice",
			"field_map": {
				"party_account_currency": "party_account_currency",
				"payment_terms_template": "payment_terms_template"
			},
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Commission Agent Report Item": {
			"doctype": "Sales Invoice Item",
			"field_map": {
				"name": "so_detail",
				"parent": "commission_agent_report",
			},
			"postprocess": update_item,
			"condition": lambda doc: doc.qty and (doc.base_amount==0 or abs(doc.billed_amt) < abs(doc.amount))
		},
		"Sales Taxes and Charges": {
			"doctype": "Sales Taxes and Charges",
			"add_if_empty": True
		},
		"Sales Team": {
			"doctype": "Sales Team",
			"add_if_empty": True
		}
	}, target_doc, postprocess, ignore_permissions=ignore_permissions)

	return doclist

@frappe.whitelist()
def make_project(source_name, target_doc=None):
	def postprocess(source, doc):
		doc.project_type = "External"
		doc.project_name = source.name

	doc = get_mapped_doc("Commission Agent Report", source_name, {
		"Commission Agent Report": {
			"doctype": "Project",
			"validation": {
				"docstatus": ["=", 1]
			},
			"field_map":{
				"name" : "commission_agent_report",
				"base_grand_total" : "estimated_costing",
			}
		},
	}, target_doc, postprocess)

	return doc

@frappe.whitelist()
def get_payment_entry(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	doc = frappe.get_doc(dt, dn)
	if flt(doc.per_billed, 2) > 0:
		frappe.throw(_("Can only make payment against unbilled {0}").format(dt))

	party_type = "Customer"

	# party account
	party_account = get_party_account(party_type, doc.get(party_type.lower()), doc.company)

	party_account_currency = doc.get("party_account_currency") or get_account_currency(party_account)

	# payment type
	payment_type = "Receive"

	# amounts
	grand_total = outstanding_amount = 0
	if party_amount:
		grand_total = outstanding_amount = party_amount
	else:
		if party_account_currency == doc.company_currency:
			grand_total = flt(doc.get("base_rounded_total") or doc.base_grand_total)
		else:
			grand_total = flt(doc.get("rounded_total") or doc.grand_total)
		outstanding_amount = grand_total - flt(doc.advance_paid)

	# bank or cash
	bank = get_default_bank_cash_account(doc.company, "Bank", mode_of_payment=doc.get("mode_of_payment"),
		account=bank_account)

	if not bank:
		bank = get_default_bank_cash_account(doc.company, "Cash", mode_of_payment=doc.get("mode_of_payment"),
			account=bank_account)

	paid_amount = received_amount = 0
	if party_account_currency == bank.account_currency:
		paid_amount = received_amount = abs(outstanding_amount)
	elif payment_type == "Receive":
		paid_amount = abs(outstanding_amount)
		if bank_amount:
			received_amount = bank_amount
		else:
			received_amount = paid_amount * doc.get('conversion_rate', 1)
	else:
		received_amount = abs(outstanding_amount)
		if bank_amount:
			paid_amount = bank_amount
		else:
			# if party account currency and bank currency is different then populate paid amount as well
			paid_amount = received_amount * doc.get('conversion_rate', 1)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = party_type
	pe.party = doc.get(scrub(party_type))
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.ensure_supplier_is_not_blocked()

	pe.paid_from = party_account if payment_type=="Receive" else bank.account
	pe.paid_to = party_account if payment_type=="Pay" else bank.account
	pe.paid_from_account_currency = party_account_currency \
		if payment_type=="Receive" else bank.account_currency
	pe.paid_to_account_currency = party_account_currency if payment_type=="Pay" else bank.account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount
	pe.letter_head = doc.get("letter_head")

	if pe.party_type in ["Customer", "Supplier"]:
		bank_account = get_party_bank_account(pe.party_type, pe.party)
		pe.set("bank_account", bank_account)
		pe.set_bank_account_data()

	# only Purchase Invoice can be blocked individually
	pe.append("references", {
		'reference_doctype': dt,
		'reference_name': dn,
		"bill_no": doc.get("bill_no"),
		"due_date": doc.get("due_date"),
		'total_amount': grand_total,
		'outstanding_amount': outstanding_amount,
		'allocated_amount': outstanding_amount
	})

	pe.setup_party_account_field()
	pe.set_missing_values()
	if party_account and bank:
		pe.set_exchange_rate()
		pe.set_amounts()
	return pe

@frappe.whitelist()
def get_events(start, end, filters=None):
	"""Returns events for Gantt / Calendar view rendering.

	:param start: Start date-time.
	:param end: End date-time.
	:param filters: Filters (JSON).
	"""
	from frappe.desk.calendar import get_event_conditions
	conditions = get_event_conditions("Commission Agent Report", filters)

	data = frappe.db.sql("""
		select
			distinct `tabCommission Agent Report`.name, `tabSCommission Agent Report`.customer_name, `tabCommission Agent Report`.status,
			`tabCommission Agent Report`.billing_status
		from
			`tabCommission Agent Report`
		where `tabCommission Agent Report`.docstatus < 2
			{conditions}
		""".format(conditions=conditions), as_dict=True, update={"allDay": 0})
	return data

@frappe.whitelist()
def update_status(status, name):
	so = frappe.get_doc("Commission Agent Report", name)
	so.update_status(status)

@frappe.whitelist()
def schedule_create_report_commission_from_wb_sbs():
	now = date.today()
	nine_days = timedelta(days=8)
	two_days = timedelta(days=2)
	date_from = now - nine_days
	date_to = now - two_days
	frappe.enqueue('create_report_commission_from_wb_sbs', date_from, date_to, timeout=4500)

def create_report_commission_from_wb_sbs(date_from, date_to):

	items = get_report_items(date_from)

	car = frappe.get_doc({
				"doctype": "Commission Agent Report",
				"naming_series": "COM-.YYYY.-",
				"customer": frappe.db.get_value("WB Settings", "WB Settings", "customer"),
				"start_date": date_from,
				"end_date": date_to,
				"transaction_date": date.today(),
				"agreement": frappe.db.get_value("WB Settings", "WB Settings", "agreement"),
				"items": items,
				"company": frappe.db.get_value("WB Settings", "WB Settings", "company"),
				"taxes": [
					{
						"charge_type": "Actual",
						"account_head": frappe.db.get_value("WB Settings", "WB Settings", "account_commission"),
						"description": frappe.db.get_value("WB Settings", "WB Settings", "account_commission")
					},
					{
						"charge_type": "Actual",
						"account_head": frappe.db.get_value("WB Settings", "WB Settings", "account_logistics"),
						"description": frappe.db.get_value("WB Settings", "WB Settings", "account_logistics")
					},
					{
						"charge_type": "Actual",
						"account_head": frappe.db.get_value("WB Settings", "WB Settings", "account_storage"),
						"description": frappe.db.get_value("WB Settings", "WB Settings", "account_storage")
					}
				]
			})

	car.insert(ignore_permissions=True, ignore_mandatory=True)

def identify_item_code(data):
	article_and_color = data.sa_name.split('/')
	if len(article_and_color) == 1:
		article_and_color.append('')
	item_name = "%s-%s-%s" % (article_and_color[0], article_and_color[1], data.ts_name)
	item_list = frappe.get_list('Item', filters={'barcode': data.barcode})
	if not item_list and frappe.db.get_value("Item", filters={"item_name":item_name}):
		item = frappe.get_doc("Item", item_name)
		item.barcodes.append({'barcode': data.barcode})
	if not item_list:
		create_item_code(data, article_and_color)
	for item in frappe.get_list('Item', filters={'barcode': data.barcode}):
		item = frappe.get_doc('Item', item.name)

	item_data = {"item_code": item.item_code, "item_name": item.item_name}

	return item_data

def get_report_items(date_from):
	final_report_items = []
	date = []
	for i in range(7):
		date.append(date_from)
		date_from += timedelta(days=1)

	for rr_dt in date:
		for data in frappe.get_all('WB Sales by Sales', filters={'rr_dt': rr_dt}):
			data = frappe.get_doc('WB Sales by Sales', data.name)

			if data.supplier_oper_name in ['Логистика', 'Возврат']:
				continue

			item_data = identify_item_code(data)

			final_report_items.append({
				"item_code": item_data['item_code'],
				"item_name": item_data['item_name'],
				"qty": data.quantity,
				"rate": data.retail_amount,
				"award": data.retail_commission,
				"uom": _("Nos"),
				"description": item_data['item_code']
			})

	return final_report_items

def create_item_code(data, article_and_color):
	mws_settings = frappe.get_doc("WB Settings")

	new_brand = create_brand(data)
	new_variant_of = create_item(data, article_and_color, new_brand, mws_settings)
	new_attributes = create_attributes(data, article_and_color, item_type = 'variant_off')

	item_dict = {
			"doctype": "Item",
			"variant_of": new_variant_of,
			"brand": new_brand,
			"is_stock_item": 1,
			"item_code": "%s-%s-%s" % (article_and_color[0], article_and_color[1], data.ts_name),
			"item_name": "%s-%s-%s-%s" % (data.subject_name, article_and_color[0], article_and_color[1], data.ts_name),
			"item_group": mws_settings.item_group,
			"has_variants": 0,
			"attributes":new_attributes,
			"stock_uom": _("Nos"),
			"default_warehouse": mws_settings.warehouse,
			"barcodes": [
				{
					"barcode": data.barcode,
					"barcode_type": "EAN"
				}
			],
			"item_defaults": [
				{
					"company": mws_settings.company
				}
			]
		}
	new_item = frappe.get_doc(item_dict)
	new_item.insert(ignore_permissions=True, ignore_mandatory=True)

	create_item_price(new_item.item_code)

	frappe.db.commit()

	return new_item.name

def create_brand(data):
	if not data.brand_name:
		return None

	existing_brand = frappe.db.get_value("Brand",
		filters={"brand":data.brand_name})
	if not existing_brand:
		brand = frappe.new_doc("Brand")
		brand.brand = data.brand_name
		brand.insert()
		return brand.brand
	else:
		return existing_brand

def create_attributes(data, article_and_color, item_type):
	final_attributes = []
	if not frappe.db.get_value("Item Attribute", filters={"attribute_name":'Цвет'}):
		create_attribut('Цвет')
	
	if not frappe.db.get_value("Item Attribute", filters={"attribute_name":'Размер'}):
		create_attribut('Размер')

	attribute = ['Цвет', 'Размер']
	variant = [data.ts_name, article_and_color[1]]

	if 	item_type == 'variant_on':
		for attr in attribute:
			final_attributes.append({
				"attribute": attr
			})

	else:
		for attr in attribute:
			item_attr = frappe.get_doc("Item Attribute", attr)
			if attr == 'Цвет':
				if variant[1] != '':
					set_new_attribute_values(item_attr, variant[1])
					item_attr.save()
				final_attributes.append({"attribute": attr, "attribute_value": get_attribute_value(variant[1], attr)})
			else:
				if variant[0] != '':
					set_new_attribute_values(item_attr, variant[0])
					item_attr.save()
				final_attributes.append({"attribute": attr, "attribute_value": get_attribute_value(variant[0], attr)})

	return final_attributes

def get_attribute_value(variant_attr_val, attribute):
	attribute_value = frappe.db.sql("""select attribute_value from `tabItem Attribute Value`
		where parent = %s and (abbr = %s or attribute_value = %s)""", (attribute, variant_attr_val,
		variant_attr_val), as_list=1)
	return attribute_value[0][0] if len(attribute_value)>0 else ''

def create_attribut(name):
	igroup = frappe.new_doc("Item Attribute")
	igroup.attribute_name = name
	igroup.insert(ignore_permissions=True)

def set_new_attribute_values(item_attr, attr_value):
	if not any((d.abbr.lower() == attr_value.lower() or d.attribute_value.lower() == attr_value.lower())\
	for d in item_attr.item_attribute_values):
		item_attr.append("item_attribute_values", {
			"attribute_value": attr_value,
			"abbr": attr_value
		})

def create_item(data, article_and_color, new_brand, mws_settings):
	attributes = create_attributes(data, article_and_color, item_type = 'variant_on')
	
	existing_variant_of = frappe.db.get_value("Item", filters={"item_code":article_and_color[0]})
	
	if not existing_variant_of:
		item_dict = {
			"doctype": "Item",
			"variant_of": None,
			"brand":new_brand,
			"is_stock_item": 1,
			"item_code": article_and_color[0],
			"item_name": article_and_color[0],
			"item_group": mws_settings.item_group,
			"has_variants": 1,
			"attributes":attributes or [],
			"stock_uom": _("Nos"),
			"default_warehouse": mws_settings.warehouse,
			"item_defaults": [
				{
					"company": mws_settings.company
				}
			]
		}
		new_item = frappe.get_doc(item_dict)
		new_item.insert(ignore_permissions=True, ignore_mandatory=True)

		frappe.db.commit()

		return new_item.item_code
	else:
		return existing_variant_of

def create_item_price(item_code):
	item_price = frappe.new_doc("Item Price")
	item_price.price_list = frappe.db.get_value("WB Settings", "WB Settings", "price_list")
	item_price.price_list_rate = 0

	item_price.item_code = item_code
	item_price.insert()