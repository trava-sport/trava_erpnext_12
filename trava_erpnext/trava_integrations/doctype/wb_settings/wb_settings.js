// Copyright (c) 2021, trava and contributors
// For license information, please see license.txt

frappe.ui.form.on('WB Settings', {
	refresh: function(frm) {
		var me = this;
		frm.add_custom_button(__('Отчет склад'), function() {
			console.log("rembo")
			frm.call({
				method: "trava_erpnext.trava_integrations.doctype.wb_settings_1.wb_report_methods.get_report",
				args: {
					//"dateFrom": frappe.datetime.get_today(),
					"dateFrom": '2021-02-16',
					"reportType": 'orders',
					"doc": 'WB Orders',
					"flag": 1
				}
			});
		});
		frm.add_custom_button(__('Аутентификация на ВБ'), function() {
			console.log("rembo")
			frappe.prompt([{
				fieldtype: "Int",
				label: __("Телефон"),
				fieldname: "phone",
				reqd: 1,
				description: __('Номер должен начинаться с семерки и пишется слитно.'),
				default: 7
			}],
			(data) => {
				frm.call({
					method: "trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.wb_authentication",
					args: {
						"value": data["phone"],
						"type": "phone"
					},
					callback: function(r) {
						frappe.prompt([{
							fieldtype: "Int",
							label: __("Код"),
							fieldname: "code",
							reqd: 1
						}],
						(data) => {
							frm.call({
								method: "trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.wb_authentication",
								args: {
									"value": data["code"],
									"type": "code",
									"out_token": r.message["token"]
								},
								callback: function(r) {
									console.log("DDDDDDDDDDDDDDDDDDDDDHHHHHHHHHHHHHHHHHHHHHHH");
									frappe.msgprint(__("Аутентификация успешна"));
								}
							})
						},
						'Введите проверочный код',
						'Отправить')
					}
				})
			},
			'Введите номер телефона',
			'Отправить')
		});
		frm.add_custom_button(__('Создать товар на ВБ'), function() {
			frm.call({
				method: "trava_erpnext.trava_integrations.doctype.wb_settings.wb_report_methods.creat_product_cards"
			});
		});
		frm.add_custom_button(__('Отчет Sales by Sales Monthly'), function() {
			console.log("rembo")
			frm.call({
				method: "trava_erpnext.trava_integrations.doctype.wb_settings_1.wb_report_methods.get_report",
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
				method: "trava_erpnext.trava_integrations.doctype.wb_settings_1.wb_report_methods.get_report",
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
