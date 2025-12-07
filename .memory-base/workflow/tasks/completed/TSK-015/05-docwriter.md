---
agent: docwriter
task_id: TSK-015
status: completed
next: null
created_at: 2025-12-07T12:00:00Z
files_changed:
  - path: .memory-base/tech-docs/api.md
    action: modified
---

## Documentation Updates

Updated API documentation to reflect the new standalone order functionality with menu item options.

### Changes Made

#### 1. Updated Menu Items Section

**Location:** `.memory-base/tech-docs/api.md` - Menu > Блюда меню

**Changes:**
- Updated `POST /cafes/{cafe_id}/menu` description: price can now be set for any category (not just "extra")
- Updated `MenuItem` schema:
  - Changed price comment: "цена для любой категории; null = только в комбо"
  - Added `options: MenuItemOption[]` field for dish options

**Rationale:** Items with prices can now be ordered standalone, not just as part of combos. Options enable customization (size, spiciness, etc.).

#### 2. Added Menu Item Options Section

**Location:** `.memory-base/tech-docs/api.md` - Menu > Опции блюд

**New Content:**
- Section introduction explaining dish options functionality
- Four new endpoints:
  - `GET /cafes/{cafe_id}/menu/{item_id}/options` - list options for a dish
  - `POST /cafes/{cafe_id}/menu/{item_id}/options` - create option (manager only)
  - `PATCH /cafes/{cafe_id}/menu/{item_id}/options/{option_id}` - update option (manager only)
  - `DELETE /cafes/{cafe_id}/menu/{item_id}/options/{option_id}` - delete option (manager only)

**New Schema: MenuItemOption**
```
MenuItemOption {
  id: int
  menu_item_id: int
  name: string               # "Размер порции"
  values: string[]           # ["Стандарт", "Большая", "XL"]
  is_required: bool          # if true, user must select
}
```

**Examples Added:**
- Creating an option for a dish (POST request)
- Getting a dish with options (GET response with nested options array)

#### 3. Updated Orders Section

**Location:** `.memory-base/tech-docs/api.md` - Orders

**Major Changes:**

1. **Section Introduction:**
   - Updated to reflect three order types:
     - Combo-only (traditional)
     - Standalone items only (new)
     - Combo + standalone items (new)
     - Extras (optional, as before)

2. **POST /orders Endpoint:**
   - Changed `combo_id` from required to optional (`combo_id?: int | null`)
   - Replaced `combo_items` field with `items` field
   - New items structure supports two types:
     - `ComboItem`: `{ type: "combo", category, menu_item_id }`
     - `StandaloneItem`: `{ type: "standalone", menu_item_id, quantity, options }`
   - Updated error messages to include "missing required options"

3. **PATCH /orders Endpoint:**
   - Updated to use `items` instead of `combo_items`
   - Support for union type `[ComboItem | StandaloneItem]`

#### 4. Updated Order Schema

**Location:** `.memory-base/tech-docs/api.md` - Orders > Order schema

**Changes:**
- `combo_id: int | null` - now nullable
- `combo?: OrderCombo` - now optional (present only if combo_id specified)
- Replaced flat combo structure with `items: OrderItem[]` array

**New Types:**
```
OrderItem = ComboItem | StandaloneItem

ComboItem {
  type: "combo"
  category: string            # "soup" | "salad" | "main"
  menu_item_id: int
  menu_item_name: string
}

StandaloneItem {
  type: "standalone"
  menu_item_id: int
  menu_item_name: string
  quantity: int
  options: { [name: string]: value: string }
  price: decimal              # unit price
  subtotal: decimal           # price * quantity
}
```

#### 5. Added Order Type Examples

**Location:** `.memory-base/tech-docs/api.md` - Orders > Типы заказов

**New Examples:**
1. **Только комбо** - traditional combo order with items array
2. **Только отдельные блюда** - standalone items only (combo_id: null)
3. **Комбо + отдельные блюда** - mixed order with both types

#### 6. Updated Example Orders

**Location:** `.memory-base/tech-docs/api.md` - Orders > Примеры заказов

**Replaced single example with two comprehensive examples:**

1. **Combo Order Example (Traditional):**
   - Shows combo_id: 2 with separate combo object
   - Items array with type: "combo" for each category
   - Extras array as before
   - Total price calculation

2. **Standalone Order Example (New):**
   - Shows combo_id: null
   - Items array with type: "standalone"
   - Each item has quantity, options, price, and subtotal
   - No extras
   - Total price = sum of standalone items

#### 7. Added Validation Rules

**Location:** `.memory-base/tech-docs/api.md` - Orders > Валидация

**New Section:**
- Validation rules for combo_id presence/absence
- Item type validation based on combo_id
- Price requirement for standalone items
- Required options validation
- Option values validation (must be from MenuItemOption.values)

#### 8. Added Price Calculation Rules

**Location:** `.memory-base/tech-docs/api.md` - Orders > Расчёт цены

**New Section:**
- Formula for combo orders: `combo.price + sum(standalone_items.subtotal) + sum(extras.subtotal)`
- Formula for standalone-only: `sum(standalone_items.subtotal) + sum(extras.subtotal)`

### Documentation Consistency

All changes maintain the existing documentation style:
- API endpoint format (HTTP method, path, Auth, Body/Query/Response)
- Schema format (TypeScript-like syntax with field descriptions)
- JSON examples with comments
- Consistent terminology and structure

### Backward Compatibility Notes

The documentation reflects backward compatibility:
- Old combo orders still work (combo_id required, items with type: "combo")
- New standalone orders supported (combo_id: null, items with type: "standalone")
- Mixed orders supported (combo_id present, items with both types)

### Cross-References

The updated documentation sections reference each other:
- MenuItem schema references MenuItemOption
- Order schema references ComboItem and StandaloneItem
- Examples demonstrate all three order types
- Validation section covers all scenarios

## Summary

Successfully updated API documentation for TSK-015. All new endpoints, schemas, and usage patterns for menu item options and standalone orders are now documented with:
- 4 new menu item option endpoints
- Updated MenuItem schema with options field
- Updated Order schema with nullable combo_id and items field
- 3 new schema types (MenuItemOption, ComboItem, StandaloneItem)
- 2 comprehensive order examples
- Validation and price calculation rules

Documentation is ready for developers to implement the feature.
