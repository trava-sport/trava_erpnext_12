from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'commission_agent_report',
		'non_standard_fieldnames': {
			'Delivery Note': 'against_sales_order',
			'Journal Entry': 'reference_name',
			'Payment Entry': 'reference_name',
			'Payment Request': 'reference_name',
			'Auto Repeat': 'reference_document',
			'Maintenance Visit': 'prevdoc_docname'
		},
		'internal_links': {
			'Quotation': ['items', 'prevdoc_docname']
		},
		'transactions': [
			{
				'label': _('Fulfillment'),
				'items': ['Sales Invoice']
			},
			{
				'label': _('Projects'),
				'items': ['Project']
			},
			{
				'label': _('Payment'),
				'items': ['Payment Entry',  'Journal Entry']
			},
		]
	}