# Mapping Options and Conversions Documentation

This document provides a comprehensive overview of all options and conversions used in the `model_PDHC1H1HAR1V1_FW539224.json` mapping file.

## Overview

The mapping file contains 26 unique label/combo references:
- **22 LABEL references** (used in sensor and binary_sensor conversions)
- **4 COMBO references** (used in select options and conversions)

## Label References (with pipe delimiters)

LABEL references are used in `conversion` dictionaries for sensor and binary_sensor types. They map raw device values (coming from the device API) to human-readable strings.

### Format
```
|{MODEL}_{FW}_LABEL_{widget_key}_{VALUE_NAME}|
```

### Usage Pattern
```json
{
  "entry_name": {
    "key": "w_xxxxx",
    "type": "sensor|binary_sensor",
    "conversion": {
      "|LABEL_REFERENCE|": "human_readable_value"
    }
  }
}
```

### All LABEL References

#### pH Type Dosing (w_1f0it2vcf)
| Label Reference | Maps To | Entry |
|-----------------|---------|-------|
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it2vcf_ACID\|` | acid | ph_type_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it2vcf_ALCALYNE\|` | alcalyne | ph_type_dosing |

#### ORP Type Dosing (w_1f0it326i)
| Label Reference | Maps To | Entry |
|-----------------|---------|-------|
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it326i_LOW_\|` | low | orp_type_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it326i_HIGH\|` | high | orp_type_dosing |

#### Cl Type Dosing (w_1f0it3458)
| Label Reference | Maps To | Entry |
|-----------------|---------|-------|
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it3458_LOW_\|` | low | cl_type_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it3458_HIGH\|` | high | cl_type_dosing |

#### Peristaltic pH Dosing (w_1f0iteoja)
| Label Reference | Maps To | Entry |
|-----------------|---------|-------|
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteoja_OFF_\|` | off | peristaltic_ph_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteoja_PROPORTIONAL\|` | proportional | peristaltic_ph_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteoja_ON_OFF\|` | on_off | peristaltic_ph_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteoja_TIMED\|` | timed | peristaltic_ph_dosing |

#### Peristaltic ORP Dosing (w_1f0iteqrl)
| Label Reference | Maps To | Entry |
|-----------------|---------|-------|
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteqrl_OFF\|` | off | peristaltic_orp_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteqrl_PROPORTIONAL\|` | proportional | peristaltic_orp_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteqrl_ON_OFF\|` | on_off | peristaltic_orp_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteqrl_TIMED\|` | timed | peristaltic_orp_dosing |

#### Peristaltic Cl Dosing (w_1f0itlfoj)
| Label Reference | Maps To | Entry |
|-----------------|---------|-------|
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0itlfoj_OFF\|` | off | peristaltic_cl_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0itlfoj_PROPORTIONAL\|` | proportional | peristaltic_cl_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0itlfoj_ON_OFF\|` | on_off | peristaltic_cl_dosing |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0itlfoj_TIMED\|` | timed | peristaltic_cl_dosing |

#### Pump Running (w_1f1fng00q)
| Label Reference | Maps To | Entry |
|-----------------|---------|-------|
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f1fng00q_OFF\|` | F | pump_running |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1f1fng00q_ON\|` | O | pump_running |

#### Pump Detection (w_1hn0vte5j)
| Label Reference | Maps To | Entry |
|-----------------|---------|-------|
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1hn0vte5j_DISABLED\|` | F | pump_detection |
| `\|PDPR1H1HAR1V0_FW539224_LABEL_w_1hn0vte5j_ENABLED\|` | O | pump_detection |

## COMBO References (without pipe delimiters)

COMBO references are used in `select` type entries. They appear in both the `options` dictionary (mapping option keys to combo references) and the `conversion` dictionary (mapping combo references to display values).

### Format
```
{MODEL}_{FW}_COMBO_{widget_key}_{VALUE_NAME}
```

### Usage Pattern
```json
{
  "entry_name": {
    "key": "w_xxxxx",
    "type": "select",
    "options": {
      "numeric_key": "COMBO_REFERENCE"
    },
    "conversion": {
      "COMBO_REFERENCE": "display_value"
    }
  }
}
```

### All COMBO References

#### Flowrate Unit (w_1f0j30vam)
| Combo Reference | Option Key | Display Value | Entry |
|-----------------|------------|---------------|-------|
| `PDPR1H1HAR1V0_FW539224_COMBO_w_1f0j30vam_L_S` | 47 | L/s | flowrate_unit |
| `PDPR1H1HAR1V0_FW539224_COMBO_w_1f0j30vam_M3_H` | 50 | m3/h | flowrate_unit |

#### Water Meter Unit (w_1f3dfp59r)
| Combo Reference | Option Key | Display Value | Entry |
|-----------------|------------|---------------|-------|
| `PDPR1H1HAR1V0_FW539224_COMBO_w_1f3dfp59r_LITERS__L_` | 8 | L | water_meter_unit |
| `PDPR1H1HAR1V0_FW539224_COMBO_w_1f3dfp59r_CUBIC_METER__M__` | 9 | m³ | water_meter_unit |

## How Values Flow Through the System

### For Sensors with Conversions
1. Device API returns a raw value (e.g., a LABEL reference with pipes)
2. The `_process_sensor_value` method looks up the value in the `conversion` dictionary
3. The human-readable string is returned to the user

### For Binary Sensors with Conversions
1. Device API returns a raw value (e.g., a LABEL reference with pipes)
2. The `_process_binary_sensor_value` method looks up the value in the `conversion` dictionary
3. The value is converted to boolean (if mapped to "F" or "O")

### For Selects
1. Device API returns a numeric option key (e.g., "47")
2. The `_process_select_value` method:
   - Looks up the option key in `options` to get the COMBO reference
   - Looks up the COMBO reference in `conversion` to get the display value
3. The display value is returned to the user

When setting a select value:
1. User provides a display value (e.g., "L/s")
2. The `_set_value` method:
   - Reverse looks up through `conversion` to find the COMBO reference
   - Reverse looks up through `options` to find the numeric key
3. The numeric key is sent to the device API

## Bug Fix Applied

During the analysis, one inconsistency was found and corrected:
- **Entry**: `peristaltic_cl_dosing` (key `w_1f0itlfoj`)
- **Issue**: The "timed" conversion was using `|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteqrl_TIMED|` (from `w_1f0iteqrl`)
- **Fix**: Changed to `|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0itlfoj_TIMED|` (matching its own key)

## Summary Statistics

- Total entries in mapping: 34
- Entries with conversions: 10
- Entries with select options: 2
- Total unique LABEL references: 22
- Total unique COMBO references: 4
- Total unique references: 26

## strings.json Template

For reference, here's a template showing all label/combo references and their suggested default values:

```json
{
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it2vcf_ACID|": "ACID",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it2vcf_ALCALYNE|": "ALCALYNE",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it326i_HIGH|": "HIGH",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it326i_LOW_|": "LOW_",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it3458_HIGH|": "HIGH",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0it3458_LOW_|": "LOW_",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteoja_OFF_|": "OFF_",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteoja_ON_OFF|": "ON_OFF",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteoja_PROPORTIONAL|": "PROPORTIONAL",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteoja_TIMED|": "TIMED",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteqrl_OFF|": "OFF",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteqrl_ON_OFF|": "ON_OFF",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteqrl_PROPORTIONAL|": "PROPORTIONAL",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0iteqrl_TIMED|": "TIMED",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0itlfoj_OFF|": "OFF",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0itlfoj_ON_OFF|": "ON_OFF",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0itlfoj_PROPORTIONAL|": "PROPORTIONAL",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0itlfoj_TIMED|": "TIMED",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f0itlfoj_TIMED|": "TIMED",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f1fng00q_OFF|": "OFF",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1f1fng00q_ON|": "ON",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1hn0vte5j_DISABLED|": "DISABLED",
  "|PDPR1H1HAR1V0_FW539224_LABEL_w_1hn0vte5j_ENABLED|": "ENABLED",
  "PDPR1H1HAR1V0_FW539224_COMBO_w_1f0j30vam_L_S": "L_S",
  "PDPR1H1HAR1V0_FW539224_COMBO_w_1f0j30vam_M3_H": "M3_H",
  "PDPR1H1HAR1V0_FW539224_COMBO_w_1f3dfp59r_CUBIC_METER__M__": "CUBIC_METER__M__",
  "PDPR1H1HAR1V0_FW539224_COMBO_w_1f3dfp59r_LITERS__L_": "LITERS__L_"
}
```
