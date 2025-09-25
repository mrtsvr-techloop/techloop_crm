import frappe


@frappe.whitelist(allow_guest=True, methods=["POST"])
def chat_with_ai(**payload):
	"""Public endpoint to interact with the AI module.

	Expected JSON body (POST):
	- message: str (required)
	- session_id: str (optional) - reuse this to keep conversation context
	- agent_name: str (optional) - logical label; defaults to "crm_ai"
	- model: str (optional) - model override when local mode is used

	Response JSON (examples):
	- { "success": true, "result": { ...ai output... } }
	- { "success": false, "error": "AI module not installed" }
	"""
	try:
		# Accept POSTed JSON body if not passed as kwargs
		if not payload and frappe.request and frappe.request.method == "POST":
			payload = frappe.parse_json(frappe.request.data or {}) or {}

		message = (payload.get("message") or "").strip()
		if not message:
			frappe.response["http_status_code"] = 400
			return {"success": False, "error": "Missing required field: message"}

		session_id = (payload.get("session_id") or None) or None
		agent_name = (payload.get("agent_name") or "crm_ai").strip() or "crm_ai"
		model = (payload.get("model") or None) or None

		try:
			from ai_module import api as ai_api
		except ImportError:
			frappe.response["http_status_code"] = 501
			return {"success": False, "error": "AI module not installed"}

		# Forward to AI module; returns dict with final_output, and when in threads mode also thread_id
		result = ai_api.ai_run_agent(agent_name, message, session_id=session_id, model=model)
		frappe.response["http_status_code"] = 200
		return {"success": True, "result": result}

	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), title="crm.api.ai_module.chat_with_ai")
		frappe.response["http_status_code"] = 500
		return {"success": False, "error": str(exc)} 