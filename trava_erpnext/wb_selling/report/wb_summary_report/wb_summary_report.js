// Copyright (c) 2016, trava and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["WB Summary Report"] = {
	"filters": [
		{
			"fieldname":"warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"get_query": function() {
				const company = frappe.query_report.get_filter_value('company');
				return {
					filters: { 'company': company }
				}
			},
			"reqd": 1
		},
		{
			"fieldname":"brand",
			"label": __("Brand"),
			"fieldtype": "Link",
			"options": "Brand",
			"depends_on": "eval: doc.warehouse_storage != 1"
		},
		{
			"fieldname":"subject",
			"label": __("Subject"),
			"fieldtype": "Link",
			"options": "WB Subject",
			"depends_on": "eval: doc.warehouse_storage != 1"
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_start_date"),
			reqd: 1
		},
		{
			fieldname:"to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_end_date"),
			reqd: 1
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"depends_on": "eval: doc.warehouse_storage == 1",
			"mandatory_depends_on": "eval: doc.warehouse_storage == 1"
		},
		{
			fieldname: "range",
			label: __("Range"),
			fieldtype: "Select",
			options: [
				{ "value": "Weekly", "label": __("Weekly") },
				{ "value": "Monthly", "label": __("Monthly") },
				{ "value": "Quarterly", "label": __("Quarterly") },
				{ "value": "Yearly", "label": __("Yearly") }
			],
			default: "Monthly",
			reqd: 1
		},
		{
			"fieldname": "warehouse_storage",
			"label": __("Use the amount for warehouse storage from the Commission Agent Report)"),
			"fieldtype": "Check",
			"default": 0,
			on_change: function() {
				let filters = frappe.query_report.filters;
				let warehouse_storage = frappe.query_report.get_filter_value('warehouse_storage');
				let options = {
					1: [{ "value": "Weekly", "label": __("Weekly") }],
					0: [
						{ "value": "Weekly", "label": __("Weekly") },
						{ "value": "Monthly", "label": __("Monthly") },
						{ "value": "Quarterly", "label": __("Quarterly") },
						{ "value": "Yearly", "label": __("Yearly") }
					]
				}

				filters.forEach(d => {
					if (d.fieldname == "range") {
						d.df.options = options[warehouse_storage];
						d.set_input(d.df.options)
					}
				});

				frappe.query_report.refresh();
			}
		}
	],

	after_datatable_render: table_instance => {
		let data = table_instance.datamanager.data;
		for (let row = 0; row < data.length; ++row) {
			if (row % 2 == 0) continue;
			let data_obj = data[row];
			let index =0;
			let arr = [];
			const symbolsLength = Object.getOwnPropertySymbols(data_obj);
			const withoutSymbolLength = Object.keys(data_obj);
			let length = symbolsLength + withoutSymbolLength;
			length = length.split(',')
			for (let row = 0; row < length.length; ++row){
				arr.push(index);
				index += 1;
			}
			if (data_obj) {
				let columns_to_highlight = arr;
				columns_to_highlight.forEach(col => {
					table_instance.style.setStyle(`.dt-cell--${col + 1}-${row}`, {backgroundColor: 'rgba(37,220,2,0.2);'});
				});
			}
		}
		table_instance.style.setStyle(`.dt-scrollable`, {height: '600px;'});
	}
};
