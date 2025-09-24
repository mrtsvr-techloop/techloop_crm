// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('CRM Product Tag', {
	tag_name: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn]
		if (row.tag_name && !row.color) {
			frappe.db.get_value('CRM Product Tag Master', row.tag_name, 'color').then(r => {
				if (r && r.message && r.message.color) {
					frappe.model.set_value(cdt, cdn, 'color', r.message.color)
				}
			})
		}
	}
})
