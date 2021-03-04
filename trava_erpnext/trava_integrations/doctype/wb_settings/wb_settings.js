// Copyright (c) 2020, trava and contributors
// For license information, please see license.txt

frappe.ui.form.on('WB Settings', {
	// refresh: function(frm) {

	// }
	refresh: function(frm) {
		var me = this;
		frm.add_custom_button(__('Отчет склад'), function() {
			console.log("rembo")
			frm.call({
				method: "trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report",
				args: {
					//"dateFrom": frappe.datetime.get_today(),
					"dateFrom": '2021-02-16',
					"reportType": 'orders',
					"doc": 'WB Orders',
					"flag": 1
				}
			});
		});
		frm.add_custom_button(__('Отчет склад 2'), function() {
			console.log("rembo")
			frm.call({
				method: "trava_erpnext.trava_integrations.doctype.wb_settings.wb_settings.schedule_get_report_stocks"
			});
		});
		frm.add_custom_button(__('Отчет Sales by Sales Monthly'), function() {
			console.log("rembo")
			frm.call({
				method: "trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report",
				args: {
					//"dateFrom": frappe.datetime.get_today(),
					"dateFrom": '2020-12-01',
					"dateTo": '2021-01-09',
					"reportType": 'reportDetailByPeriod',
					"doc": 'WB Sales by Sales Monthly'
				}
			});
		});
		frm.add_custom_button(__('Отчет Sales'), function() {
			console.log("rembo")
			frm.call({
				method: "trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.get_report",
				args: {
					//"dateFrom": frappe.datetime.get_today(),
					"dateFrom": '2021-02-08',
					"dateTo": '2021-01-09',
					"reportType": 'sales',
					"doc": 'WB Sales',
					"flag": 1
				}
			});
		});
	},

	onload: function(frm) {
		if(frm.get_field("account_commission") || frm.get_field("account_logistics") || frm.get_field("account_storage")) {
			frm.set_query("account_commission", function(doc) {
				var account_type = ["Tax", "Chargeable", "Expense Account"];

				return {
					query: "erpnext.controllers.queries.tax_account_query",
					filters: {
						"account_type": account_type,
						"company": doc.company
					}
				}
			});

			frm.set_query("account_logistics", function(doc) {
				var account_type = ["Tax", "Chargeable", "Expense Account"];

				return {
					query: "erpnext.controllers.queries.tax_account_query",
					filters: {
						"account_type": account_type,
						"company": doc.company
					}
				}
			});

			frm.set_query("account_storage", function(doc) {
				var account_type = ["Tax", "Chargeable", "Expense Account"];

				return {
					query: "erpnext.controllers.queries.tax_account_query",
					filters: {
						"account_type": account_type,
						"company": doc.company
					}
				}
			});

			frm.set_query("cost_center", function(doc) {
				return {
					filters: {
						'company': doc.company,
						"is_group": 0
					}
				}
			});
		}
	},

	customer: function(frm) {
		frm.doc.agreement = '';
		var me = this;
		frm.set_query('agreement', function() {
			return {
				filters: {
					customer: frm.doc.customer
				}
			};
		});
	}
});
