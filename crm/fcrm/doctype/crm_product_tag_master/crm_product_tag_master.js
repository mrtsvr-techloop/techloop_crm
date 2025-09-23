// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('CRM Product Tag Master', {
	tag_name: function (frm) {
		if (frm.doc.tag_name) {
			frm.set_value("tag_name", frm.doc.tag_name.trim());
		}
	},
	
	refresh: function(frm) {
		if (!frm.doc.color) {
			frm.set_value("color", "#3b82f6");
		}
	}
}); 