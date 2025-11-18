from crm.install import add_default_quick_filters


def execute():
	# Force update to ensure default quick filters (ID, order_date, delivery_date) are set
	add_default_quick_filters(force=True)

