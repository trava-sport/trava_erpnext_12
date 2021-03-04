// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Commission Agent Report'] = {
	onload: function(me) {
		me.page.add_menu_item(__("Add Report Commission"), function() {
			frappe.call({
				method: "trava_erpnext.sale_commission.doctype.commission_agent_report.commission_agent_report.create_report_commission_from_wb_sales_by_sales"
			});
		});
	},
};
