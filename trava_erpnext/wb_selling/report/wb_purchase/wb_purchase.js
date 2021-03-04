// Copyright (c) 2016, trava and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["WB Purchase"] = {
	"filters": [
		{
			"fieldname":"brand",
			"label": __("Brand"),
			"fieldtype": "Link",
			"options": "Brand",
		},
		{
			"label": __("Days until next purchase"),
			"fieldtype": "Int",
			"fieldname": "days_until_next_purchase",
			"width": 70,
			"reqd": 1
		},
		{
			"label": __("Days from purchase to delivery"),
			"fieldtype": "Int",
			"fieldname": "days_from_purchase_to_delivery",
			"width": 70,
			"reqd": 1
		},
		{
			"label": __("Qty of recent days for which you need to calculate the average implementation"),
			"fieldtype": "Int",
			"fieldname": "delta_days",
			"width": 70,
			"reqd": 1
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
