{% include 'erpnext/selling/sales_common.js' %};


frappe.provide("trava_erpnext.selling.");
trava_erpnext.selling.SellingCommission = erpnext.selling.SellingController.extend({
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

	agreement: function() {
		var me = this;
		if (this.frm.doc.agreement) {
			frappe.call({
				"method": "frappe.client.get_value",
				"args": {
					"doctype": "Agreement",
					"name": this.frm.doc.agreement,
					"fieldname":'agreement_type'
				},
				"callback": function(response) {
					me.frm.doc.agreement_type = response.message.agreement_type
					console.log(response.message.agreement_type);
				}
			});
		}
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

	calculate_totals: function() {
		this._super();
		if(!in_list(["Commission Agent Report", "Sales Invoice"], this.frm.doc.doctype)) {
			return
		}
		this.calculate_commission_agent();

		if(in_list(["Commission Agent Report"], this.frm.doc.doctype)){
			this.calculate_amount_principal();
		}
	},

	calculate_commission_agent: function() {
		var me = this;

		this.frm.doc.commission_agents_remuneration = this.frm.doc.base_commission_agents_remuneration = 0.0;

		$.each(this.frm.doc["items"] || [], function(i, item) {
			me.frm.doc.commission_agents_remuneration += item.award;
			me.frm.doc.base_commission_agents_remuneration += item.base_award;
			});

		frappe.model.round_floats_in(this.frm.doc, ["commission_agents_remuneration", "base_commission_agents_remuneration"]);

		let tax_count = this.frm.doc["taxes"] ? this.frm.doc["taxes"].length : 0;
		let tax = this.frm.doc["taxes"];

		frappe.db.get_value("WB Settings", {'name': 'WB Settings'}, "account_commission", (r) => {
			console.log(r)
			console.log(r.account_commission)
			me.frm.doc.wb_setting_commission = r.account_commission;
			if (r.account_commission === null) {
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

		this.frm.refresh_fields();
	},

	calculate_amount_principal: function() {
		this.frm.doc.amount_principal = flt(this.frm.doc.grand_total);
		this.frm.doc.base_amount_principal = flt(this.frm.doc.base_grand_total);

		this.frm.refresh_fields();
	}
});