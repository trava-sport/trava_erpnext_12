// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt
{% include 'frappe/apublic/js/frappe/form/grid.js' %};

console.log ("::::: CUSTOM:::: me::::");

GridTy = Grid1.extend({
	setup_allow_bulk_edit() {
		var me = this;
		if(this.frm && this.frm.get_docfield(this.df.fieldname).allow_bulk_edit) {
			// download
			me.setup_download();

			// upload
			frappe.flags.no_socketio = true;
			$(this.wrapper).find(".grid-upload").removeClass('hidden').on("click", function() {
				new frappe.ui.FileUploader({
					as_dataurl: true,
					allow_multiple: false,
					on_success(file) {
						var data = frappe.utils.csv_to_array(frappe.utils.get_decoded_string(file.dataurl));
						// row #2 contains fieldnames;
						var fieldnames = data[2];
						console.log(data)
						console.log(fieldnames)

						me.frm.clear_table(me.df.fieldname);
						$.each(data, function(i, row) {
							console.log(row)
							if(i > 6) {
								let code = '';
								let item_code = '';
								var blank_row = true;
								$.each(row, function(ci, value) {
									if(value) {
										blank_row = false;
										return false;
									}
								});

								if(!blank_row) {
									$.each(row, function(ci, value) {
										var fieldname = fieldnames[ci];
										console.log(fieldname)
										if(fieldname === 'item_code') {
											item_code = ci;
											console.log(item_code)
										}
										if(fieldname === 'barcode' && value && !code) {
											code = value;
											console.log(code)
										}
										if(fieldname === 'wb_id' && value) {
											code = value;
											console.log(code)
										}

										if(fieldname === 'wb_id' && value && !row[1]) {
											frappe.call({
												method: "erpnext.selling.page.point_of_sale.point_of_sale.search_serial_or_batch_or_barcode_number",
												args: { search_value: value }
											}).then(r => {
												const data_itemf = r && r.message;
											});

											if(data_item.item_code) { arr[0] = data_item.item_code }
										}
									});
								}

								if(!blank_row) {
									frappe.call({
										method: "erpnext.selling.page.point_of_sale.point_of_sale.search_serial_or_batch_or_barcode_number",
										args: { search_value: code }
									}).then(r => {
										const data_item = r && r.message;

										if(data_item.item_code) { row[item_code] = data_item.item_code }

										console.log(row)
										console.log(me.df.fieldname)
										var d = me.frm.add_child(me.df.fieldname);
										console.log(d)
										$.each(row, function(ci, value) {
											var fieldname = fieldnames[ci];
											console.log(fieldname)
											var df = frappe.meta.get_docfield(me.df.options, fieldname);
											console.log(df)

											// convert date formatting
											if(df.fieldtype==="Date" && value) {
												value = frappe.datetime.user_to_str(value);
											}

											if(df.fieldtype==="Int" || df.fieldtype==="Check") {
												value = cint(value);
											}

											d[fieldnames[ci]] = value;

											me.frm.refresh_field(me.df.fieldname);
										});
									});
								}
							}
						});

						frappe.msgprint({message:__('Table updated'), title:__('Success'), indicator:'green'})
					}
				});
				return false;
			});
		}
	}
	
});

$.extend(cur_frm.cscript, new GridTy({frm: cur_frm}));
