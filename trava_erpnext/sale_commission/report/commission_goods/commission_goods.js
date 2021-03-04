// Copyright (c) 2016, trava and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Commission Goods"] = {
	"filters": [
		{
			"fieldname":"on_date",
			"label": __("On date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			fieldname: "didnt_report_back",
			label: __("Didn't report back"),
			fieldtype: "Select",
			options: [
				{ "value": "Any", "label": __("Any") },
				{ "value": "Greater than zero", "label": __("Greater than zero") },
				{ "value": "Zero", "label": __("Zero") }
			],
			default: "Any",
			reqd: 1
		},
		{
			"fieldname":"item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"get_query": function() {
				return {
					query: "erpnext.controllers.queries.item_query"
				}
			}
		},
		{
			"fieldname":"item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname":"agreement",
			"label": __("Agreement"),
			"fieldtype": "Link",
			"options": "Agreement",
			"get_query": function() {
				const customer = frappe.query_report.get_filter_value('customer');
				return {
					filters: { 
						'customer': customer,
						'agreement_type': 'Commission'
					}
				}
			}
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
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
