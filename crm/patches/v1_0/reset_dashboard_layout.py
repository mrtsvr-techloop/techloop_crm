import frappe
from crm.fcrm.doctype.crm_dashboard.crm_dashboard import create_default_manager_dashboard


def execute():
	"""Reset dashboard layout to new default layout with new charts."""
	create_default_manager_dashboard(force=True)

