// Copyright (c) 2016, trava and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["WB Price"] = {
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
			"fieldname":"company",
			"label": __("Company for valuation rate selection"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname":"brand",
			"label": __("Brand"),
			"fieldtype": "Link",
			"options": "Brand"
		},
		{
			"label": __("New price"),
			"fieldtype": "Int",
			"fieldname": "new_price",
			"width": 70
		},
		{
			"label": __("New discount"),
			"fieldtype": "Int",
			"fieldname": "new_discount",
			"width": 70
		},
		{
			"label": __("New promo code"),
			"fieldtype": "Int",
			"fieldname": "new_promo_code_discount",
			"width": 70
		},
		/* {
			"label": __("From the new price"),
			"fieldtype": "Int",
			"fieldname": "from_new_price",
			"width": 100
		},
		{
			"label": __("To the new price"),
			"fieldtype": "Int",
			"fieldname": "to_new_price",
			"width": 100
		},
		{
			"label": __("From the new discount"),
			"fieldtype": "Int",
			"fieldname": "from_new_discount",
			"width": 100
		},
		{
			"label": __("To the new discount"),
			"fieldtype": "Int",
			"fieldname": "to_new_discount",
			"width": 100
		},
		{
			"label": __("From the new promo code discount"),
			"fieldtype": "Int",
			"fieldname": "from_new_promo_code_discount",
			"width": 70
		},
		{
			"label": __("To the new promo code discount"),
			"fieldtype": "Int",
			"fieldname": "to_new_promo_code_discount",
			"width": 70
		},
		{
			"label": __("From the turnover rate"),
			"fieldtype": "Float",
			"fieldname": "from_turnover_rate",
			"width": 100
		},
		{
			"label": __("To the turnover rate"),
			"fieldtype": "Float",
			"fieldname": "to_turnover_rate",
			"width": 100
		},
		{
			"label": __("From the current discount"),
			"fieldtype": "Int",
			"fieldname": "from_current_discount",
			"width": 100
		},
		{
			"label": __("To the current discount"),
			"fieldtype": "Int",
			"fieldname": "to_current_discount",
			"width": 100
		},
		{
			"label": __("From the current promo code"),
			"fieldtype": "Int",
			"fieldname": "from_current_promo_code",
			"width": 70
		},
		{
			"label": __("To the current promo code"),
			"fieldtype": "Int",
			"fieldname": "to_current_promo_code",
			"width": 70
		},
		{
			"label": __("From the current price without discounts"),
			"fieldtype": "Float",
			"fieldname": "from_current_price",
			"width": 100
		},
		{
			"label": __("To the current price without discounts"),
			"fieldtype": "Float",
			"fieldname": "to_current_price",
			"width": 100
		},
		{
			"label": __("From the current price with discount"),
			"fieldtype": "Float",
			"fieldname": "from_current_price_discount",
			"width": 100
		},
		{
			"label": __("To the current price with discount"),
			"fieldtype": "Float",
			"fieldname": "to_current_price_discount",
			"width": 100
		},
		{
			"label": __("From the current price with discount and promo code"),
			"fieldtype": "Float",
			"fieldname": "from_current_price_discount_promo_code",
			"width": 100
		},
		{
			"label": __("To the current price with discount and promo code"),
			"fieldtype": "Float",
			"fieldname": "to_current_price_discount_promo_code",
			"width": 100
		},
		{
			"label": __("From the new price with discount"),
			"fieldtype": "Float",
			"fieldname": "from_new_price_discount",
			"width": 100
		},
		{
			"label": __("To the new price with discount"),
			"fieldtype": "Float",
			"fieldname": "to_new_price_discount",
			"width": 100
		},
		{
			"label": __("From the new price with discount and promo code"),
			"fieldtype": "Float",
			"fieldname": "from_new_price_disc_promo_code",
			"width": 100
		},
		{
			"label": __("To the new price with discount and promo code"),
			"fieldtype": "Float",
			"fieldname": "to_new_price_disc_promo_code",
			"width": 100
		},
		{
			"label": __("From current net profit"),
			"fieldtype": "Float",
			"fieldname": "from_current_net_profit",
			"width": 100
		},
		{
			"label": __("To current net profit"),
			"fieldtype": "Float",
			"fieldname": "to_current_net_profit",
			"width": 100
		},
		{
			"label": __("From new net profit"),
			"fieldtype": "Float",
			"fieldname": "from_new_net_profit",
			"width": 100
		},
		{
			"label": __("To new net profit"),
			"fieldtype": "Float",
			"fieldname": "to_new_net_profit",
			"width": 100
		}, */
		{
			"label": __("The desired net profit"),
			"fieldtype": "Float",
			"fieldname": "desired_net_profit",
			"width": 60
		},
		{
			"fieldname":"from_date_sales",
			"label": __("From the date of sales"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1
		},
		{
			"fieldname":"to_date_sales",
			"label": __("To the date of sales"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		/* {
			"label": __("From sales"),
			"fieldtype": "Float",
			"fieldname": "from_sales",
			"width": 100
		},
		{
			"label": __("To sales"),
			"fieldtype": "Float",
			"fieldname": "to_sales",
			"width": 100
		},
		{
			"label": __("From the remnant"),
			"fieldtype": "Float",
			"fieldname": "from_remnant",
			"width": 100
		},
		{
			"label": __("To the remnant"),
			"fieldtype": "Float",
			"fieldname": "to_remnant",
			"width": 100
		}, */
		{
			fieldname: "unmarketable",
			label: __("Unmarketable"),
			fieldtype: "Select",
			options: [
				{ "value": "Все", "label": __("Все") },
				{ "value": "Да", "label": __("Да") },
				{ "value": "Нет", "label": __("Нет") }
			]
		},
		{
			"fieldname": "calculation_new_price_discounts",
			"label": __("Calculation of the new price with discounts from the new retail price(default calculation from the standard price)"),
			"fieldtype": "Check",
			"default": 0
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
