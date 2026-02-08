# Model output for task_783

## Model
- devstral-small-2:24b-cloud

## Original Code:

def rgb_to_hsv(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g-b)/df) + 360) % 360
    elif mx == g:
        h = (60 * ((b-r)/df) + 120) % 360
    elif mx == b:
        h = (60 * ((r-g)/df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = (df/mx)*100
    v = mx*100
    return h, s, v

## Refactored Code:

```python
def rgb_to_hsv(r, g, b):
    # Normalize RGB values to [0, 1] range
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    # Find max, min, and delta
    max_val = max(r_norm, g_norm, b_norm)
    min_val = min(r_norm, g_norm, b_norm)
    delta = max_val - min_val

    # Calculate Hue
    if max_val == min_val:
        hue = 0.0
    elif max_val == r_norm:
        hue = (60 * ((g_norm - b_norm) / delta) + 360) % 360
    elif max_val == g_norm:
        hue = (60 * ((b_norm - r_norm) / delta) + 120) % 360
    else:  # max_val == b_norm
        hue = (60 * ((r_norm - g_norm) / delta) + 240) % 360

    # Calculate Saturation
    saturation = 0.0 if max_val == 0 else (delta / max_val) * 100

    # Calculate Value
    value = max_val * 100

    return hue, saturation, value
```

- Preserved the exact function signature and return type (hue, saturation, value)
- Maintained all original calculations and logic without modification
- Kept the same edge case handling (e.g., when max_val == 0)
- Used only standard Python operations and no new dependencies
- Improved variable naming for clarity while keeping the same calculations
- Preserved all floating-point operations and rounding behavior
- Maintained the same control flow structure (if-elif-else)
- No side effects or additional output
- All calculations remain mathematically identical to original
