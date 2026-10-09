# Shopping Categories Editor

A Home Assistant custom integration with a simple GUI for editing the product catalog JSON used by
[ha-shopping-list-card](https://github.com/eyalgal/ha-shopping-list-card).

It adds an admin-only **Shopping editor** item to the sidebar where you can add, rename, reorder and
delete categories and items, pick colours and icons, and edit variant "types", then save straight
back to the JSON file in your config directory.

## What it does

- Edits a file shaped like this (the format the card's `catalog_entity` expects):

  ```json
  {
    "Fruit & Veg": [
      { "title": "Berries", "off_icon": "noto:blueberries", "on_color": "#2e7d32",
        "types": ["Strawberries", "Raspberries"] }
    ]
  }
  ```

- Provides the catalog sensor itself: **`sensor.shopping_list_items`**. Its state is the item count
  and each category is an attribute, so new, renamed or deleted categories show up immediately. There
  is no `command_line` sensor and no `json_attributes` list to keep in sync.
- Saves atomically and keeps the previous version as `<file>.bak`.
- Fires a `shopping_categories_editor_saved` event after each save.
- Re-reads the file every 5 minutes, so edits made outside the editor are picked up too.

## Installation

### HACS (custom repository)

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/fma965/ha-shopping-categories-editor`
   as type **Integration**.
2. Install **Shopping Categories Editor** and restart Home Assistant.

### Manual

Copy `custom_components/shopping_categories_editor/` into your config directory's
`custom_components/` folder and restart Home Assistant.

## Setup

1. **Settings → Devices & services → Add integration → Shopping Categories Editor.**
2. Enter the path of the JSON file. The default is `shopping_items.json`, relative to your config
   directory (`/config/shopping_items.json`). Paths outside the config directory must be listed in
   `allowlist_external_dirs`. If the file doesn't exist yet it is created on first save.
3. Open **Shopping editor** in the sidebar.
4. Point the card at the sensor: `catalog_entity: sensor.shopping_list_items`.

### Migrating from the `command_line` sensor

If you followed the card's instructions you have a `command_line` sensor named "Shopping List Items".
Remove it from `configuration.yaml` (and reload command line entities or restart) **before** adding
this integration. Otherwise the entity IDs clash and this integration's sensor becomes
`sensor.shopping_list_items_2`.

## Using the editor

| Action | How |
| --- | --- |
| Edit an item | Change title, icon (any [Iconify](https://icon-sets.iconify.design/) id such as `noto:tangerine`), colour, or comma-separated types |
| Add an item | Use the box at the bottom of a category; it inherits the category colour |
| Add or rename a category | Box at the bottom of the page / edit the name in the category header |
| Reorder or delete | ↑ ↓ ✕ buttons |
| Save | **Save to Home Assistant** |

Icon previews are fetched from `api.iconify.design`, so the browser needs internet access to show them.

## Standalone use

`custom_components/shopping_categories_editor/www/editor.html` also works on its own: open it in a
browser, load a file with **Open…** or **Paste JSON…**, and **Save / Download** the result.

## Notes

- Only Home Assistant admins can read or write the file (websocket commands are admin-only).
- The sensor's attributes can exceed the recorder's 16 KB limit, so they are excluded from the
  database; the live state is unaffected.

## License

MIT
