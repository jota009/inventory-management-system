<!-- f82dc594-0d2a-4f14-b9a7-b3f4297f5ff2 c1ba3638-aaa8-477e-ab33-988d6e7ddc82 -->
# Inventory App – Senior Dev Handoff

## 1. Context and Tech Stack

- Flask-based inventory app for high-volume printing facilities (production materials: paper, toner, oils, cleaning supplies, spare parts).
- Backend: `app.py` (Flask 3.x, SQLite via `sqlite3`, basic helper functions and routes).
- Database: `inventory.db` with two main tables:
- `inventory(id, name, category, subcategory, current_quantity, minimum_threshold, unit, supplier, notes, last_updated)`
- `usage_history(id, item_id, quantity_used, remaining_quantity, date_used, notes)`
- Frontend: Jinja2 templates under `templates/` with Bootstrap 5 and Font Awesome icons.

## 2. Key Files

- `app.py`
- Initializes DB (`init_db()`), including `inventory` and `usage_history` tables.
- Helper functions: `get_db_connection`, `get_all_items`, `get_item_by_id`, `get_low_stock_items`, `update_item_quantity`, `record_usage`.
- Core routes: `index`, `add_item`, `edit_item`, `use_item`, `low_stock`, `import_csv`, `export_csv`, `delete_item`, `api_stock_status`.
- `templates/index.html`
- Dashboard with Quick Add modal, category filters, inventory table, and action buttons.
- Recently updated to:
- Add `Subcategory` column to the table (between Category and Stock Level).
- Show subcategory badge or `-` if not present.
- Add Spare Parts subcategory dropdown in the Quick Add modal (common consumables).
- `templates/use_item.html`
- Currently present but effectively empty; this is the next feature area to implement.

## 3. Recent Completed Changes (State as of Handoff)

- Database schema:
- `inventory` table rebuilt so `subcategory` is column 3 (after `category`).
- `usage_history` table already exists and is used by the backend.
- Backend changes in `app.py`:
- `add_item` route now reads `subcategory` from forms and includes it in the `INSERT` statement.
- `edit_item` route reads `subcategory` and includes it in the `UPDATE` statement.
- `use_item` route is already defined and integrated with `usage_history`:
- GET: loads `item = get_item_by_id(item_id)` and renders `use_item.html`.
- POST: reads `quantity_used` and optional `notes` from the form, validates against `item['current_quantity']`, computes `new_quantity`, calls `update_item_quantity`, and records the usage via `record_usage`.
- Frontend changes in `index.html`:
- Inventory table:
- Shows `Subcategory` column: badge if `item.subcategory` present, otherwise a muted dash.
- `Actions` column includes three buttons:
- Use item: `href="{{ url_for('use_item', item_id=item.id) }}"` with minus icon.
- Edit item.
- Delete item (with confirm dialog).
- Quick Add modal:
- Category buttons (Toner & Ink, Paper & Media, Machine Oil, Cleaning Supplies, Spare Parts, Other).
- For `Spare Parts`, a subcategory dropdown appears (required), with predefined consumable parts.

## 4. Known Gaps / Open Work

1. `use_item.html` template is not implemented.

- Current behavior: clicking the minus icon in the Actions column navigates to `/use_item/<id>`.
- Since `use_item.html` is empty, the UX for logging usage is incomplete, and Flask may raise `TemplateNotFound` or render a blank page depending on the file content.

2. UX alignment for "Use" action.

- The intent (per product owner) is: the minus icon in Actions is for quickly logging a usage event (often a single use of that item).
- Backend is more general (can log any `quantity_used`), which is good, but the UI should make the 1-unit use very fast and obvious.

3. Reporting / visibility of `usage_history`.

- Data is being stored via `record_usage`, but there is currently no route or template to view usage history.

## 5. Design Intent For `use_item` Flow

- Goal: keep the app simple, accessible, and fast for operators on the floor.
- Expected UX when operator clicks the minus icon from the table:
- See a small, focused page or modal showing:
- Item name, category, subcategory (if present), current quantity, and unit.
- A form to confirm usage:
- `quantity_used` (default to 1, required, min 1).
- Optional `notes` (e.g., which press, which shift, reason for unusual usage).
- Primary action: "Log Usage".
- Secondary action: "Cancel" / "Back to Inventory".
- On submit:
- If requested quantity exceeds stock, show a clear error and do not modify inventory.
- Otherwise, decrement `current_quantity`, record into `usage_history`, and redirect back to `index` with a success flash message.

## 6. Recommended Next Steps For The Next Senior Dev

### 6.1 Implement `use_item.html` template

- Location: `templates/use_item.html`.
- Minimum structure:
- Extend `base.html` for consistent layout.
- Show item context:
- Name, category, subcategory, current quantity, minimum threshold, unit.
- Usage form:
- Method: POST to `/use_item/<item_id>` (current route already expects this).
- Fields:
- `quantity_used` (number input, default value 1, min 1, max = current_quantity for client-side hint).
- `notes` (textarea, optional).
- Buttons:
- Submit: "Log Usage".
- Link/button back to `index`.
- Render flashed messages for any errors or success (standard Flask pattern already in base template).

### 6.2 Align the "minus" action with desired UX

- Keep the existing route and logic in `app.py` as-is (already robust), but ensure the UI matches expectations:
- For typical operators, primary path should be: one click on minus icon → page pre-filled with quantity 1 → submit.
- If more advanced usage is needed (logging multiple units at once), they can manually change the quantity before submit.
- Consider, in a later iteration, offering two patterns:
- Current pattern (default for now): minus opens `use_item.html` with a simple form.
- Future enhancement: quick one-click POST that decrements by 1 without a confirmation screen (requires CSRF and method considerations).

### 6.3 (Optional) Add a lightweight usage history view

- Since `usage_history` is already populated, a simple read-only page would add a lot of value for supervisors.
- Suggested route and template:
- Route: `/usage_history` in `app.py` that joins `usage_history` with `inventory` for item names.
- Template: `templates/usage_history.html` listing recent usage events (item name, quantity used, remaining quantity, date, notes).
- This is not required to make `use_item` functional, but it is a natural follow-up.

## 7. Notes For Future Refactors

- Centralize repeated SQL column lists.
- `export_csv` and `import_csv` do not yet know about `subcategory` and `usage_history`; a later pass could standardize export/import behavior.
- Consider wrapping DB access in a small repository layer or using an ORM for larger-scale evolution.
- Security is currently appropriate for an internal tool, but if this is ever exposed more broadly, add CSRF protection and authentication.

## 8. Implementation Todos (for tracking)

- implement-use-item-template: Create `use_item.html` with a simple, focused form to log item usage (quantity and notes) and show core item details.
- align-use-action-ux: Ensure the minus icon path (from `index.html`) flows cleanly into the `use_item` page with quantity defaulted to 1 and clear messaging.
- add-usage-history-view: Optionally add a read-only `usage_history` listing page for supervisors, using the existing `usage_history` table.