# import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import Contact


class CustomContact(Contact):
	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': _('First Name'),
				'type': 'Data',
				'key': 'first_name',
				'width': '12rem',
			},
			{
				'label': _('Last Name'),
				'type': 'Data',
				'key': 'last_name',
				'width': '12rem',
			},
			{
				'label': _('Company Name'),
				'type': 'Data',
				'key': 'company_name',
				'width': '14rem',
			},
			{
				'label': _('Email Address'),
				'type': 'Data',
				'key': 'email_id',
				'width': '14rem',
			},
			{
				'label': _('Mobile No'),
				'type': 'Data',
				'key': 'mobile_no',
				'width': '12rem',
			},
			{
				'label': _('Created On'),
				'type': 'Datetime',
				'key': 'creation',
				'width': '12rem',
			},
		]
		rows = [
			"name",
			"first_name",
			"last_name",
			"company_name",
			"email_id",
			"mobile_no",
			"creation",
			"modified",
			"image",
		]
		return {'columns': columns, 'rows': rows}
	
	@staticmethod
	def get_quick_filters():
		# Return empty list to disable quick filters for Contact
		return []
