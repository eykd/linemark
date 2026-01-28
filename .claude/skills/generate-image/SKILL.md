---
name: generate-image
description: Generate images using Gemini 2.5 Flash Image (Nano Banana) via gemimg. Use when users request AI image generation, image editing, multi-image blending, style transfer, product mockups, character consistency work, or text/logo rendering in images. Triggers on requests like "generate an image", "create a picture", "edit this photo", "combine these images", "make a logo".
---

# Generate Image with gemimg

Generate and edit images using `gemimg` package wrapping Gemini 2.5 Flash Image (Nano Banana).

## Setup

```bash
pip install gemimg --break-system-packages
```

Requires `GEMINI_API_KEY` environment variable or pass directly.

## Quick Start

```python
from gemimg import GemImg

g = GemImg()  # Uses GEMINI_API_KEY from env

# Text-to-image
gen = g.generate("A kitten with purple-and-green fur.", save_dir="/mnt/user-data/outputs")

# Edit existing image
gen_edit = g.generate("Change the background to a beach.", gen.image, save_dir="/mnt/user-data/outputs")

# Multi-image blend (max 3 images recommended)
gen_blend = g.generate("Place the person from image 1 into the scene from image 2.", 
                       ["person.png", "background.png"], save_dir="/mnt/user-data/outputs")
```

## Key Parameters

```python
g.generate(
    prompt,                    # Required: descriptive text
    images=None,               # Optional: PIL.Image, path, or list for editing/blending
    aspect_ratio="1:1",        # "1:1", "16:9", "9:16", "4:3", "3:4"
    save=True,                 # Auto-save generated image
    save_dir=".",              # Output directory
    webp=True,                 # WEBP format (smaller) vs PNG
)
```

Returns `GeneratedImage` with `.image` (PIL.Image) attribute.

## Prompting Essentials

**CRITICAL: Use complete descriptive sentences, not keywords.**

| Bad | Good |
|-----|------|
| `cat, armor, silver` | `A cat wearing ornate silver plate armor with falcon-wing shoulder guards.` |
| `man, jacket, red` | `Change the man's blue jacket to a vibrant red leather jacket.` |

**Core principles:**
- Frame positively: "a quiet empty street" not "a street with no cars"
- Use Markdown lists for complex multi-part requests
- Add professional terms: "golden hour lighting", "85mm f/1.8 lens", "bokeh background"
- Include artistic style: "in the style of Studio Ghibli", "oil on canvas"

**For detailed prompting techniques → see `references/prompting.md`**

## Common Workflows

### Character Consistency
Upload clear source image, reference subject explicitly:
```python
g.generate("Place this person in a 1960s beehive hairdo and retro outfit.", source_image)
```

### Text/Logo Rendering
Specify font style, color, placement:
```python
g.generate("Create a logo with 'The Daily Grind' in clean minimalist sans-serif. Coffee bean icon above text.")
```

### Multi-Turn Editing
Build complex images incrementally:
```python
gen1 = g.generate("Add a bookshelf to the back wall.", room_image)
gen2 = g.generate("Now add this sofa in a natural position.", [gen1.image, sofa_image])
gen3 = g.generate("Change walls to sage green, preserving furniture.", gen2.image)
```

## Limitations & Workarounds

| Issue | Solution |
|-------|----------|
| Aspect ratio ignored | Use "frame hack": upload blank image in desired ratio, ask model to fill it |
| Prompt ignored | Simplify to single instruction; rephrase with different vocabulary |
| Quality degrades after edits | Limit to 2-3 edits; upscale as final step |
| Style transfer fails | Generate new image in target style rather than transforming existing |
| Text typos | Provide pre-rendered text as input image, ask to composite |

## Grid Generation (Cost-Effective)

Generate multiple images in one call with Nano Banana Pro:

```python
from gemimg import GemImg, Grid

g = GemImg(model="gemini-3-pro-image-preview")
grid = Grid(rows=2, cols=2, image_size="2K")

gen = g.generate(
    "Generate a 2x2 grid of 4 distinct images of cherry trees in: Oil Painting, Watercolor, Digital Art, Pencil Sketch",
    grid=grid,
    save_dir="/mnt/user-data/outputs"
)
# gen.subimages contains the 4 individual images
```
