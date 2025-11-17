# Copyright (c) 2025, Techloop and Contributors
# License: MIT. See LICENSE

from frappe import _
from frappe.www.login import get_context as frappe_get_context

no_cache = True


def get_context(context):
	# Estendi il context di Frappe
	frappe_get_context(context)
	
	# Disabilita login con email link
	context["login_with_email_link"] = False
	
	# Assicura che header e footer siano nascosti
	context["no_header"] = True
	context["no_footer"] = True
	context["show_footer_on_login"] = False
	
	return context

