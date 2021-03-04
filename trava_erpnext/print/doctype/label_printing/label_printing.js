// Copyright (c) 2021, trava and contributors
// For license information, please see license.txt
frappe.ui.form.on('Label Printing Item', {
	item_code: function(frm,cdt,cdn) {
		var row = locals[cdt][cdn];
		frappe.db.get_value("Item", row.item_code, "item_name", (r) => {
			row.item_name = r.item_name;
		});
		refresh_field("item_name", cdn, "items");
	}
});