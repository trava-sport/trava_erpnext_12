// Copyright (c) 2020, trava and contributors
// For license information, please see license.txt
{% include 'trava_erpnext/public/js/commission_sales.js' %};
{% include 'erpnext/selling/sales_common.js' %};


frappe.provide("trava_erpnext.selling");

frappe.ui.form.on('Commission Agent Report', {
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Delivery Note': 'Delivery Note',
			'Pick List': 'Pick List',
			'Sales Invoice': 'Invoice',
			'Material Request': 'Material Request',
			'Purchase Order': 'Purchase Order',
			'Project': 'Project',
			'Payment Entry': "Payment",
			'Work Order': "Work Order"
		}
		frm.add_fetch('customer', 'tax_id', 'tax_id');

		frm.set_query('company_address', function(doc) {
			if(!doc.company) {
				frappe.throw(__('Please set Company'));
			}

			return {
				query: 'frappe.contacts.doctype.address.address.address_query',
				filters: {
					link_doctype: 'Company',
					link_name: doc.company
				}
			};
		})

		frm.set_query("bom_no", "items", function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			return {
				filters: {
					"item": row.item_code
				}
			}
		});
	},
	refresh: function(frm) {
		if(frm.doc.docstatus === 1 && frm.doc.status !== 'Closed'
			&& flt(frm.doc.per_billed, 6) < 100) {
			frm.add_custom_button(__('Update Items'), () => {
				erpnext.utils.update_child_items({
					frm: frm,
					child_docname: "items",
					child_doctype: "Commission Agent Report Detail",
					cannot_add_row: false,
				})
			});
		}
	},
	onload: function(frm) {
		if (!frm.doc.transaction_date){
			frm.set_value('transaction_date', frappe.datetime.get_today())
		}

		frm.set_query('project', function(doc, cdt, cdn) {
			return {
				query: "erpnext.controllers.queries.get_project_name",
				filters: {
					'customer': doc.customer
				}
			}
		});

		cur_frm.cscript.calculate_taxes_and_totals();
	},
});

trava_erpnext.selling.SalesCommissionController = trava_erpnext.selling.SellingCommission.extend({
	onload: function(doc, dt, dn) {
		this._super();
	},
	
	refresh: function(doc, dt, dn) {
		var me = this;
		this._super();

		if (doc.docstatus==1) {

			if(this.frm.has_perm("submit")) {
				if(doc.status === 'On Hold') {
				   // un-hold
				   this.frm.add_custom_button(__('Resume'), function() {
					   me.frm.cscript.update_status('Resume', 'Draft')
				   }, __("Status"));

				   if(flt(doc.per_delivered, 6) < 100 || flt(doc.per_billed) < 100) {
					   // close
					   this.frm.add_custom_button(__('Close'), () => this.close_sales_order(), __("Status"))
				   }
				}
			   	else if(doc.status === 'Closed') {
				   // un-close
				   this.frm.add_custom_button(__('Re-open'), function() {
					   me.frm.cscript.update_status('Re-open', 'Draft')
				   }, __("Status"));
			   }
			}
			if(doc.status !== 'Closed') {
				if(doc.status !== 'On Hold') {
					if (this.frm.has_perm("submit")) {
						if(flt(doc.per_billed) < 100) {
							// hold
							this.frm.add_custom_button(__('Hold'), () => this.hold_sales_order(), __("Status"))
							// close
							this.frm.add_custom_button(__('Close'), () => this.close_sales_order(), __("Status"))
						}
					}

					const order_is_a_sale = ["Sales", "Shopping Cart"].indexOf(doc.order_type) !== -1;
					const order_is_maintenance = ["Maintenance"].indexOf(doc.order_type) !== -1;
					// order type has been customised then show all the action buttons
					const order_is_a_custom_sale = ["Sales", "Shopping Cart", "Maintenance"].indexOf(doc.order_type) === -1;

					// sales invoice
					if(flt(doc.per_billed, 6) < 100) {
						this.frm.add_custom_button(__('Sales Invoice'), () => me.make_sales_invoice(), __('Create'));
					}

					// project
					if(flt(doc.per_delivered, 2) < 100) {
							this.frm.add_custom_button(__('Project'), () => this.make_project(), __('Create'));
					}
				}
				// payment request
				if(flt(doc.per_billed)<100) {
					this.frm.add_custom_button(__('Payment'), () => this.make_payment_entry(), __('Create'));
				}
				this.frm.page.set_inner_btn_group_as_primary(__('Create'));
			}
		}
	},

	make_sales_invoice: function() {
		frappe.model.open_mapped_doc({
			method: "trava_erpnext.sale_commission.doctype.commission_agent_report.commission_agent_report.make_sales_invoice",
			frm: this.frm
		})
	},

	make_project: function() {
		frappe.model.open_mapped_doc({
			method: "trava_erpnext.sale_commission.doctype.commission_agent_report.commission_agent_report.make_project",
			frm: this.frm
		})
	},

	get_method_for_payment: function(){
		var method = "trava_erpnext.sale_commission.doctype.commission_agent_report.commission_agent_report.get_payment_entry";
		if(cur_frm.doc.__onload && cur_frm.doc.__onload.make_payment_via_journal_entry){
			method= "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_order";
		}

		return method
	},

	hold_sales_order: function(){
		var me = this;
		var d = new frappe.ui.Dialog({
			title: __('Reason for Hold'),
			fields: [
				{
					"fieldname": "reason_for_hold",
					"fieldtype": "Text",
					"reqd": 1,
				}
			],
			primary_action: function() {
				var data = d.get_values();
				frappe.call({
					method: "frappe.desk.form.utils.add_comment",
					args: {
						reference_doctype: me.frm.doctype,
						reference_name: me.frm.docname,
						content: __('Reason for hold: ')+data.reason_for_hold,
						comment_email: frappe.session.user,
						comment_by: frappe.session.user_fullname
					},
					callback: function(r) {
						if(!r.exc) {
							me.update_status('Hold', 'On Hold')
							d.hide();
						}
					}
				});
			}
		});
		d.show();
	},
	close_sales_order: function(){
		this.frm.cscript.update_status("Close", "Closed")
	},
	update_status: function(label, status){
		var doc = this.frm.doc;
		var me = this;
		frappe.ui.form.is_saving = true;
		frappe.call({
			method: "erpnext.selling.doctype.sales_order.sales_order.update_status",
			args: {status: status, name: doc.name},
			callback: function(r){
				me.frm.reload_doc();
			},
			always: function() {
				frappe.ui.form.is_saving = false;
			}
		});
	}
});
$.extend(cur_frm.cscript, new trava_erpnext.selling.SalesCommissionController({frm: cur_frm}));