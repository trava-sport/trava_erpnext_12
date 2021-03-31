{% include 'erpnext/selling/sales_common.js' %};


frappe.provide("trava_erpnext.selling.");
trava_erpnext.selling.SellingCommission = erpnext.selling.SellingController.extend({
	setup: function() {
		frappe.flags.hide_serial_batch_dialog = true
		this._super();
		frappe.ui.form.on(this.frm.doctype + " Return Item", "rate", function(frm, cdt, cdn) {
			var item = frappe.get_doc(cdt, cdn);
			var has_margin_field = frappe.meta.has_field(cdt, 'margin_type');

			frappe.model.round_floats_in(item, ["rate", "price_list_rate"]);

			if(item.price_list_rate) {
				if(item.rate > item.price_list_rate && has_margin_field) {
					// if rate is greater than price_list_rate, set margin
					// or set discount
					item.discount_percentage = 0;
					item.margin_type = 'Amount';
					item.margin_rate_or_amount = flt(item.rate - item.price_list_rate,
						precision("margin_rate_or_amount", item));
					item.rate_with_margin = item.rate;
				} else {
					item.discount_percentage = flt((1 - item.rate / item.price_list_rate) * 100.0,
						precision("discount_percentage", item));
					item.discount_amount = flt(item.price_list_rate) - flt(item.rate);
					item.margin_type = '';
					item.margin_rate_or_amount = 0;
					item.rate_with_margin = 0;
				}
			} else {
				item.discount_percentage = 0.0;
				item.margin_type = '';
				item.margin_rate_or_amount = 0;
				item.rate_with_margin = 0;
			}
			item.base_rate_with_margin = item.rate_with_margin * flt(frm.doc.conversion_rate);

			cur_frm.cscript.set_gross_profit(item);
			cur_frm.cscript.calculate_taxes_and_totals();

		});
	},

	customer: function() {
		this.frm.doc.agreement = '';
		this._super();
		var me = this;
		this.frm.set_query('agreement', function() {
			return {
				filters: {
					customer: me.frm.doc.customer
				}
			};
		});
	},

    change_grid_labels: function(company_currency) {
		this._super(company_currency);

		// toggle columns
		var item_grid = this.frm.fields_dict["items"].grid;
		$.each(["base_award"], function(i, fname) {
			if(frappe.meta.get_docfield(item_grid.doctype, fname))
				item_grid.set_column_disp(fname, me.frm.doc.currency != company_currency);
		});
	},

	change_form_labels: function(company_currency) {
		this._super(company_currency);

		// toggle fields
		this.frm.toggle_display(["base_commission_agents_remuneration", "base_amount_principal"],
		this.frm.doc.currency != company_currency);
	},

	award: function(doc, cdt, cdn) {
		$.each(this.frm.doc["items"] || [], function(i, item) {
			frappe.model.round_floats_in(item);
			item.base_award = flt(item.award * item.conversion_rate)
		});
		
		this.calculate_commission_agent();
		this.calculate_taxes_and_totals();
	},

	calculate_item_values: function() {
		this._super();
		var me = this;
		if (!this.discount_amount_applied && this.frm.doc["items_return"]) {
			$.each(this.frm.doc["items_return"] || [], function(i, item) {
				frappe.model.round_floats_in(item);
				item.net_rate = item.rate;

				if ((!item.qty) && me.frm.doc.is_return) {
					item.amount = flt(item.rate * -1, precision("amount", item));
				} else {
					item.amount = flt(item.rate * item.qty, precision("amount", item));
				}

				item.net_amount = item.amount;
				item.item_tax_amount = 0.0;
				item.total_weight = flt(item.weight_per_unit * item.stock_qty);

				me.set_in_company_currency(item, ["price_list_rate", "rate", "amount", "net_rate", "net_amount"]);
			});
		}
	},

	calculate_net_total: function() {
		var me = this;
		this.frm.doc.total_qty = this.frm.doc.total = this.frm.doc.base_total = this.frm.doc.net_total = this.frm.doc.base_net_total = 0.0;

		$.each(this.frm.doc["items"] || [], function(i, item) {
			me.frm.doc.total += item.amount;
			me.frm.doc.total_qty += item.qty;
			me.frm.doc.base_total += item.base_amount;
			me.frm.doc.net_total += item.net_amount;
			me.frm.doc.base_net_total += item.base_net_amount;
			});

		let total_return = 0.0;
		let total_qty_return = 0.0;
		let base_total_return = 0.0;
		let net_total_return = 0.0;
		let base_net_total_return = 0.0;

		$.each(this.frm.doc["items_return"] || [], function(i, item) {
			total_return += item.amount;
			total_qty_return += item.qty;
			base_total_return += item.base_amount;
			net_total_return += item.net_amount;
			base_net_total_return += item.base_net_amount;
			});

		me.frm.doc.total -= total_return;
		me.frm.doc.total_qty -= total_qty_return;
		me.frm.doc.base_total -= base_total_return;
		me.frm.doc.net_total -= net_total_return;
		me.frm.doc.base_net_total -= base_net_total_return;
		me.frm.doc.refund_amount = total_return;

		frappe.model.round_floats_in(this.frm.doc, ["total", "base_total", "net_total", "base_net_total", "refund_amount"]);
	},

	calculate_totals: function() {
		this._super();
		if(in_list(["Commission Agent Report", "Sales Invoice"], this.frm.doc.doctype)) {
			this.calculate_commission_agent();
		}
	},

	calculate_commission_agent: function() {
		var me = this;

		let commission_agents_remuneration = 0.0;
		let base_commission_agents_remuneration = 0.0;
		let commission_agents_remuneration_return = 0.0;
		let base_commission_agents_remuneration_return = 0.0;
		this.frm.doc.commission_agents_remuneration = this.frm.doc.base_commission_agents_remuneration = 0.0;

		$.each(this.frm.doc["items"] || [], function(i, item) {
			commission_agents_remuneration += item.award;
			base_commission_agents_remuneration += item.base_award;
			});
			
		$.each(this.frm.doc["items_return"] || [], function(i, item) {
			commission_agents_remuneration_return += item.award;
			base_commission_agents_remuneration_return += item.base_award;
			});

		me.frm.doc.commission_agents_remuneration = commission_agents_remuneration - commission_agents_remuneration_return
		me.frm.doc.base_commission_agents_remuneration = base_commission_agents_remuneration - base_commission_agents_remuneration_return

		frappe.model.round_floats_in(this.frm.doc, ["commission_agents_remuneration", "base_commission_agents_remuneration"]);

		let tax_count = this.frm.doc["taxes"] ? this.frm.doc["taxes"].length : 0;
		let tax = this.frm.doc["taxes"];

		frappe.db.get_value("WB Settings", {'name': 'WB Settings'}, ["account_commission", "enable_wb"], (r) => {
			console.log(r)
			console.log(r.account_commission)
			me.frm.doc.wb_setting_commission = r.account_commission;
			if (r.account_commission === null && r.enable_wb === 1) {
				frappe.throw(__("Пожалуйста, укажите комиссию по счету в настройках интеграции с Вайлдберриз."));
			};
		});

		let wb_settings = this.frm.doc.wb_setting_commission;
		if (wb_settings === null) {
			frappe.throw(__("Пожалуйста, укажите комиссию по счету в настройках интеграции с Вайлдберриз."));
		}
		if(tax_count) {
			for (var prop in tax) {
				if(tax[prop].account_head === wb_settings) {
					tax[prop].tax_amount = -me.frm.doc.commission_agents_remuneration
				}
			}
		}

		this.frm.doc.amount_principal = flt(this.frm.doc.total - me.frm.doc.commission_agents_remuneration);
		this.frm.doc.base_amount_principal = flt(this.frm.doc.base_total - me.frm.doc.base_commission_agents_remuneration);

		this.frm.refresh_fields();
	}
});