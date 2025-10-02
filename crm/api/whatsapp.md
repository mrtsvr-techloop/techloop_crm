### WhatsApp integration (whatsapp.py)

A minimal overview of how WhatsApp messages are linked to CRM records, what events are emitted, and which fields are required.

### Overview
- **Auto-linking**: Incoming/Outgoing `WhatsApp Message` docs are auto-linked to a `CRM Lead` or `CRM Deal` based on phone number.
- **Realtime updates**: After save, a realtime event is published so UIs can refresh the message thread.
- **Agent notifications**: For incoming messages, assigned users of the linked Lead/Deal are notified.
- **APIs**: Endpoints to fetch messages, create messages (text/media), send template messages, and react to a message.

### Hooks in this module
- **`validate(doc, method)`**: When a `WhatsApp Message` is validated, fills `reference_doctype` and `reference_name` by matching `from`/`to` number to a `CRM Deal` first, then `CRM Lead`.
- **`on_update(doc, method)`**: On save, publishes a realtime event on channel `whatsapp_message` with `reference_doctype` and `reference_name`, then calls `notify_agent(doc)`.
- **`notify_agent(doc)`**: For incoming messages, notifies assigned users of the linked record via CRM notifications.

### Public API (whitelisted)
- **`is_whatsapp_enabled()`**: Returns True/False based on `WhatsApp Settings.enabled` (also returns False if the DocType does not exist).
- **`is_whatsapp_installed()`**: Returns True if `WhatsApp Settings` DocType exists.
- **`get_whatsapp_messages(reference_doctype, reference_name)`**:
  - Returns all `WhatsApp Message` docs linked to the given record.
  - If the record is a `CRM Deal`, it also includes messages linked to the associated `CRM Lead`.
  - Enriches Template messages with rendered `template`, `header`, and `footer` (using `WhatsApp Templates`).
  - Attaches reaction info to the reacted message, and adds reply context to replies.
- **`create_whatsapp_message(reference_doctype, reference_name, message, to, attach, reply_to, content_type='text')`**:
  - Creates a `WhatsApp Message`. If `reply_to` is provided, marks it as a reply and links by `reply_to_message_id`.
  - Returns the created document name.
- **`send_whatsapp_template(reference_doctype, reference_name, template, to)`**:
  - Creates a Template-type `WhatsApp Message` linked to a `WhatsApp Templates` record.
  - Returns the created document name.
- **`react_on_whatsapp_message(emoji, reply_to_name)`**:
  - Creates a reaction (`content_type = 'reaction'`) to an existing message.
  - Returns the created document name.

### Helper logic
- **`get_lead_or_deal_from_number(number)`**: Normalizes a phone number and looks up a match on `CRM Deal` first, then `CRM Lead` (prefers non-converted leads).
- **`parse_mobile_no(mobile_no)`**: Keeps only `+` and digits. Example: `+91 (766) 667 6666` → `+917666676666`.
- **`parse_template_parameters(string, parameters)`**: Replaces `{{1}}`, `{{2}}`, ... with provided values.
- **`get_from_name(message)`**: Best-effort display name for message sender (uses primary contact on Deal, or lead name).

### Required DocTypes and fields
- **WhatsApp Settings**
  - `enabled` (Check): toggles module availability via `is_whatsapp_enabled()`.

- **WhatsApp Message** (referenced/created by this module)
  - Linking: `reference_doctype` (e.g., `CRM Lead` or `CRM Deal`), `reference_name` (name of the linked doc)
  - Direction: `type` (`Incoming` | `Outgoing`), `to`, `from`
  - Content: `message` (text), `content_type` (e.g., `text`, `reaction`), `attach` (optional)
  - Template support: `message_type` (`Template` when sending templates), `use_template` (Check), `template` (Link to `WhatsApp Templates`), `template_parameters` (JSON), `template_header_parameters` (JSON)
  - Threading: `is_reply` (Check), `reply_to_message_id` (ID of the message being replied to), `message_id` (provider ID), `status` (optional)
  - System: `name`, `owner`, `creation` (standard fields)

- **WhatsApp Templates**
  - `template_name`, `template` (body), `header` (optional), `footer` (optional)

- **CRM Lead**
  - `mobile_no` (string), `first_name`, `last_name`, `converted` (Check)

- **CRM Deal**
  - `mobile_no` (string)
  - `lead` (Link to `CRM Lead`), `lead_name` (string)
  - `contacts` (child table) with fields like `is_primary` (Check), `full_name`, `mobile_no`

### Phone number normalization and matching
- Numbers are normalized to `+<digits>` using `parse_mobile_no`.
- The lookup compares the sanitized input against a sanitized DB value that strips non-digits and prefixes `+` in the SQL expression.
- Recommended: store and pass numbers with a country code (e.g., `+15551234567`).

### Realtime and notifications
- Realtime channel: `whatsapp_message` (payload includes `reference_doctype` and `reference_name`).
- For incoming messages, assigned users of the linked `CRM Lead`/`CRM Deal` receive a CRM notification with a WhatsApp notification type. 