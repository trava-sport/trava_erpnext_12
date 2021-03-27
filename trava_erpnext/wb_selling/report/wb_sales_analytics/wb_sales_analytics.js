// Copyright (c) 2016, trava and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["WB Sales Analytics"] = {
	"filters": [
		{
			"fieldname":"brand",
			"label": __("Brand"),
			"fieldtype": "Link",
			"options": "Brand"
		},
		{
			"fieldname":"subject",
			"label": __("Subject"),
			"fieldtype": "Link",
			"options": "WB Subject"
		},
		{
			"fieldname":"all_subject_except",
			"label": __("All subject except"),
			"fieldtype": "Link",
			"options": "WB Subject"
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
