// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('CRM Product Tag', {
	tag: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.tag) {
			// Fetch the color from the tag master
			frappe.db.get_value('CRM Product Tag Master', row.tag, 'color')
			.then(r => {
				if (r.message && r.message.color) {
					frappe.model.set_value(cdt, cdn, 'tag_color', r.message.color);
					frm.refresh_field('product_tags');
				}
			});
		}
	}
});
