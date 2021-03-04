// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Packing Slip', {
	refresh: function(frm) {
		var me = this;
		frm.add_custom_button(__("Получить товар из накладной"), function() {
			cur_frm.cscript.get_items_button();
		});
	},

	scan_barcode: function(frm) {
		let scan_barcode_field = frm.fields_dict["scan_barcode"];

		let show_description = function(idx, exist = null) {
			if (exist) {
				frappe.show_alert({
					message: __('Row #{0}: Qty increased by 1', [idx]),
					indicator: 'green'
				});
			} else {
				frappe.show_alert({
					message: __('Row #{0}: Item added', [idx]),
					indicator: 'green'
				});
			}
		}

		if(frm.doc.scan_barcode) {
			frappe.call({
				method: "erpnext.selling.page.point_of_sale.point_of_sale.search_serial_or_batch_or_barcode_number",
				args: { search_value: frm.doc.scan_barcode }
			}).then(r => {
				const data = r && r.message;
				if (!data || Object.keys(data).length === 0) {
					frappe.show_alert({
						message: __('Cannot find Item with this Barcode'),
						indicator: 'red'
					});
					return;
				}

				let cur_grid = frm.fields_dict.items.grid;

				let row_to_modify = null;
				const existing_item_row = frm.doc.items.find(d => d.item_code === data.item_code);
				const blank_item_row = frm.doc.items.find(d => !d.item_code);

				if (existing_item_row) {
					row_to_modify = existing_item_row;
				} else if (blank_item_row) {
					row_to_modify = blank_item_row;
				}

				console.log(existing_item_row);
				console.log("blank_item_row");
				console.log(blank_item_row);
				if (!row_to_modify) {
					// add new row
					row_to_modify = frappe.model.add_child(frm.doc, cur_grid.doctype, 'items');
				}

				show_description(row_to_modify.idx, row_to_modify.item_code);

				console.log(frm.from_barcode);
				frm.from_barcode = frm.from_barcode ? frm.from_barcode + 1 : 1;
				console.log(frm.from_barcode);
				console.log(row_to_modify.doctype);
				console.log(row_to_modify.name);
				console.log(data.item_code);
				frappe.model.set_value(row_to_modify.doctype, row_to_modify.name, {
					item_code: data.item_code,
					qty: (row_to_modify.qty || 0) + 1
				});

				['serial_no', 'batch_no', 'barcode'].forEach(field => {
					if (data[field] && frappe.meta.has_field(row_to_modify.doctype, field)) {

						let value = (row_to_modify[field] && field === "serial_no")
							? row_to_modify[field] + '\n' + data[field] : data[field];

						frappe.model.set_value(row_to_modify.doctype,
							row_to_modify.name, field, value);
					}
				});

				scan_barcode_field.set_value('');
				refresh_field("items");
			});
		}
		return false;
	}
});

cur_frm.cscript.onload_post_render = function(doc, cdt, cdn) {
}

cur_frm.cscript.get_items = function() {
	
}

cur_frm.cscript.get_items_button = function() {
	return this.frm.call({
		doc: this.frm.doc,
		method: "get_items",
		callback: function(r) {
			if(!r.exc) cur_frm.refresh();
		}
	});
}

// TODO: validate gross weight field
