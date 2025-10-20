# Table Filter Documentation

## Overview

The `table` filter renders list data as formatted HTML tables with powerful column configuration and filter expression support. It integrates seamlessly with your existing NDR Core template language and filter system.

## Basic Usage

### Simple Table (Auto-detect columns)

```
{contributors|table}
```

This will auto-detect columns from the first object and generate headers automatically.

### With Custom Configuration

```
{contributors|table:cols="[role,contributors]",headers="[Role,Contributors]",tstyle=striped}
```

**Important:** Array parameters (cols, headers, expr) must be quoted to prevent the parser from splitting on internal commas.

## Syntax Guide

### Array Parameters
Array parameters must be enclosed in quotes. Use single quotes inside double quotes (or vice versa) for nested quotes:

```
✅ Correct:   cols="[role,contributors]"
✅ Correct:   expr="['capitalize','badge:bg=byval']"
✅ Correct:   expr='["capitalize","badge:bg=byval"]'
❌ Incorrect: cols=[role,contributors]  (will cause parsing errors)
```

### Why Quote Arrays?
The template parser splits parameters by commas. Without quotes, it splits inside your arrays:
- `cols=[a,b,c]` is incorrectly split into `cols=[a`, `b`, `c]`
- `cols="[a,b,c]"` is correctly treated as a single parameter

### Filter Expressions in Arrays
When using filter expressions with parameters, use the opposite quote type:
```
expr="['capitalize','badge:field=person,color=byval']"
```
or
```
expr='["capitalize","badge:field=person,color=byval"]'
```

## Configuration Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `cols` | Array (quoted) | Column keys to display (supports dot-notation) | Auto-detect from first item |
| `headers` | Array (quoted) | Header labels for columns | Capitalized column keys |
| `expr` | Array (quoted) | Filter expressions to apply to each column | None |
| `tstyle` | String | Table style: `plain`, `small`, `striped`, `small-striped`, `bordered`, `hover`, `sm-striped` | `plain` |
| `tclass` | String | Additional CSS classes for the table | None |
| `rowclass` | String | CSS class for table rows | None |
| `limit` | Integer | Maximum number of rows to display | No limit |
| `empty` | String | Text when list is empty | "No data available" |
| `empty_cell` | String | Text for empty cells | "" (empty string) |
| `join` | String | Separator when cell contains a list | ", " |
| `responsive` | Boolean | Wrap in responsive div | `true` |

## Examples

### Example 1: Basic Contributors Table

**Data:**
```json
{
  "contributors": [
    {
      "role": "Domain Expert",
      "contributors": ["pema_frick"]
    },
    {
      "role": "Data Curator",
      "contributors": ["pema_frick"]
    },
    {
      "role": "Annotator",
      "contributors": ["sven_burkhardt", "pema_frick"]
    }
  ]
}
```

**Template:**
```
{contributors|table}
```

**Output:** A simple table with "Role" and "Contributors" columns, where the contributors cell shows comma-separated values.

---

### Example 2: With Filters on Columns

**Template:**
```
{contributors|table:cols="[role,contributors]",headers="[Role,Contributors]",expr="['capitalize','badge:field=person,tt=__field__']"}
```

**Result:**
- First column (role): Applies `capitalize` filter → "Domain expert", "Data curator"
- Second column (contributors): Applies `badge` filter → Renders each contributor as a badge with tooltip

**Note:** Use single quotes inside double quotes (or vice versa) for filter expressions to avoid escaping.

---

### Example 3: Styled Table with Custom Classes

**Template:**
```
{contributors|table:tstyle=sm-striped,tclass=table-hover,rowclass=align-middle}
```

**Output:** A small, striped table with hover effect and vertically centered row content.

---

### Example 4: Nested Data with Dot-Notation

**Data:**
```json
{
  "users": [
    {
      "name": "John Doe",
      "profile": {
        "email": "john@example.com",
        "role": "Admin"
      }
    },
    {
      "name": "Jane Smith",
      "profile": {
        "email": "jane@example.com",
        "role": "User"
      }
    }
  ]
}
```

**Template:**
```
{users|table:cols="[name,profile.email,profile.role]",headers="[Name,Email,Role]"}
```

**Result:** Table with three columns extracting nested values using dot-notation.

---

### Example 5: With Multiple Filter Expressions

**Template:**
```
{data|table:cols="[name,email,status]",headers="[Name,Email,Status]",expr="['upper','linkify:url=mailto:[email]','badge:bg=gradient']"}
```

**Result:**
- Name: Uppercase
- Email: Converted to mailto link
- Status: Badge with gradient color

---

### Example 6: Limited Rows with Custom Empty Messages

**Template:**
```
{contributors|table:limit=5,empty="No contributors found",empty_cell=N/A}
```

**Result:** Shows only first 5 rows, displays "No contributors found" if empty list, and "N/A" for empty cells.

---

### Example 7: Custom List Separator

When a cell contains a list, you can customize how items are joined:

**Template:**
```
{contributors|table:cols="[role,contributors]",expr="['capitalize','badge:field=person']",join="<br>"}
```

**Result:** Contributors in a cell are separated by line breaks instead of commas.

---

### Example 8: Non-Responsive Table

**Template:**
```
{data|table:responsive=false}
```

**Result:** Table without the responsive wrapper div.

---

## Advanced Use Cases

### Combining Multiple Filters

You can chain multiple filters in the `expr` parameter for more complex formatting:

```
{data|table:cols="[price]",expr="['format:.2f']"}
```

### Using Context Variables in Filter Expressions

The filter expressions have access to the full row data context:

```
{data|table:expr="['linkify:url=/details/[id]']"}
```

This creates links using the `id` field from each row.

### Complex Badge Configuration

```
{contributors|table:cols="[role,contributors]",expr="['capitalize','badge:field=person,color=byval,tt=__field__']"}
```

This renders badges with:
- Colors based on the value (byval)
- Tooltips from the field definition

---

## Table Styles Reference

| Style | CSS Classes | Description |
|-------|------------|-------------|
| `plain` | `table` | Basic table |
| `small` or `sm` | `table table-sm` | Compact table |
| `striped` | `table table-striped` | Zebra-striped rows |
| `small-striped` or `sm-striped` | `table table-sm table-striped` | Compact striped table |
| `bordered` | `table table-bordered` | Bordered table |
| `hover` | `table table-hover` | Hoverable rows |

You can combine styles with `tclass`:
```
{data|table:tstyle=striped,tclass="table-hover table-bordered"}
```

---

## Error Handling

The filter provides helpful error messages:

- **Wrong data type:** "Table filter requires a list, got dict"
- **Mismatched headers:** "Headers count (2) must match columns count (3)"
- **Mismatched expressions:** "Expressions count (2) must match columns count (3)"

---

## Best Practices

1. **Always specify columns explicitly** for production code to avoid issues if data structure changes
2. **Use meaningful headers** instead of relying on auto-generated ones
3. **Test filter expressions** on single values first before applying to table columns
4. **Use `limit`** parameter for large datasets to improve performance
5. **Leverage dot-notation** for nested data instead of pre-processing data
6. **Use `empty_cell`** for better UX when data might be incomplete

---

## Quick Syntax Reference

Here are the correct syntaxes for your use case:

### Basic Table
```
{contributors|table}
```

### With Columns and Headers
```
{contributors|table:cols="[role,contributors]",headers="[Role,Contributors]"}
```

### With Filters Applied to Columns
```
{contributors|table:cols="[role,contributors]",headers="[Role,Contributors]",expr="['capitalize','badge:bg=byval']"}
```

### Full Example (Your Use Case)
```
{contributors|table:cols="[role,contributors]",headers="[Role,Contributors]",expr="['capitalize','badge:field=person,tt=__field__']",tstyle=striped}
```

### Key Syntax Rules
1. **Quote all array parameters**: `cols="[a,b]"` not `cols=[a,b]`
2. **Use opposite quotes inside**: `expr="['filter1','filter2']"` or `expr='["filter1","filter2"]'`
3. **Named attributes only**: All parameters use `name=value` format (no positional parameters)

---

## Implementation Notes

- The filter processes the entire list at once (not item-by-item)
- Filter expressions are applied in the context of each row
- Lists within cells are automatically joined with the separator
- Empty or None values are handled gracefully
- Bootstrap table classes are used for styling compatibility
- The responsive wrapper ensures mobile-friendly tables

---

## Your Original Example

Using your contributors example:

**Data:**
```json
{
  "contributors": [
    {"role": "Domain Expert", "contributors": ["pema_frick"]},
    {"role": "Data Curator", "contributors": ["pema_frick"]},
    {"role": "Annotator", "contributors": ["sven_burkhardt", "pema_frick"]},
    {"role": "Analyst", "contributors": ["pema_frick", "sorin_marti"]},
    {"role": "Engineer", "contributors": ["pema_frick", "sorin_marti"]}
  ]
}
```

**Simple Version:**
```
{contributors|table}
```

**Advanced Version:**
```
{contributors|table:cols="[role,contributors]",headers="[Role,Contributors]",expr="['capitalize','badge:field=person,tt=__field__']",tstyle=striped}
```

**Output HTML:**
```html
<div class="table-responsive">
  <table class="table table-striped">
    <thead>
      <tr>
        <th>Role</th>
        <th>Contributors</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Domain expert</td>
        <td>
          <span class="badge ..." data-toggle="tooltip" title="...">Pema Frick</span>
        </td>
      </tr>
      <tr>
        <td>Data curator</td>
        <td>
          <span class="badge ..." data-toggle="tooltip" title="...">Pema Frick</span>
        </td>
      </tr>
      <tr>
        <td>Annotator</td>
        <td>
          <span class="badge ..." data-toggle="tooltip" title="...">Sven Burkhardt</span>,
          <span class="badge ..." data-toggle="tooltip" title="...">Pema Frick</span>
        </td>
      </tr>
      <!-- ... more rows ... -->
    </tbody>
  </table>
</div>
```
