# Prompting Best Practices for Nano Banana

## Foundational Principles

### Descriptive Sentences Over Keywords
The model interprets semantic meaning, not keyword matching. Provide context, nuance, and relational information.

**Transform keywords into sentences:**
- `elf, armor, fantasy, silver` → `An ornate set of elven plate armor engraved with delicate silver leaf patterns, with a high collar and falcon-wing-shaped shoulder guards.`
- `logo, Merry Christmas, elegant font` → `Design a logo with the text 'Merry Christmas!' in an elegant serif font. Keep the overall design clean and modern.`

### Positive Framing
Describe what you want, not what to exclude. Negative constraints are unreliable.
- ❌ `a street with no cars`
- ✅ `a quiet empty street`

### Formula for Text-to-Image
`<Create/generate an image of> <subject> <action> <scene>`

Example progression:
1. `Create an image of a cat napping`
2. `Create an image of a cat napping in a sunbeam on a windowsill`

---

## Professional Photography Lexicon

Use technical terms for precise control:

### Lighting
| Term | Effect | Example |
|------|--------|---------|
| Golden Hour | Soft, warm, diffused light | `...illuminated by soft golden hour light streaming through a window` |
| Cinematic Lighting | High-contrast, moody, dramatic | `...with dramatic cinematic lighting from a desk lamp casting long shadows` |
| Rembrandt Lighting | Classic portrait lighting with shadow triangle | `...with Rembrandt lighting creating depth` |

### Lens & Aperture
| Term | Effect | Example |
|------|--------|---------|
| Bokeh | Soft blur in out-of-focus areas | `...with a soft, creamy bokeh background` |
| 85mm f/1.8 | Portrait lens, shallow depth of field | `...captured with an 85mm f/1.8 lens` |
| Wide angle | Expansive, dramatic perspective | `...shot with a wide-angle lens` |

### Composition
| Term | Effect | Example |
|------|--------|---------|
| Rule of Thirds | Balanced, engaging placement | `...composed using the rule of thirds` |
| Leading Lines | Draw eye to subject | `...with leading lines guiding to the subject` |

### Film Stocks
Invoke specific aesthetics:
- `...with the nostalgic aesthetic of being shot on Kodak Portra 400 film`
- `...like Fujifilm Velvia with saturated colors`

---

## Artistic Style References

### By Artist
- `...in the expressive, post-impressionist style of Vincent van Gogh`
- `...in the dreamlike surrealist style of Salvador Dalí`

### By Movement/Medium
- `...rendered with bold geometric shapes in the style of Cubism`
- `...as a traditional Japanese Sumi-e ink wash painting`
- `...in the style of Art Nouveau with flowing organic lines`

### By Genre/Aesthetic
- `...with a high-tech, Blade Runner-inspired cyberpunk aesthetic`
- `...in the enchanting style of Studio Ghibli`
- `...photorealistic, award-winning National Geographic photography`

---

## Advanced Techniques

### Markdown-Structured Complex Prompts
For multi-requirement images, use dashed lists:

```
Create an image featuring three kittens.

All kittens MUST follow these descriptions EXACTLY:
- Left: black-and-silver fur, wearing blue denim overalls and baseball hat
- Middle: white-and-gold fur with gold goatee, wearing golden monocle
- Right: pink-and-green fur, wearing sports jersey

Composition requirements:
- All kittens positioned using rule of thirds
- All kittens laying prone, facing camera
- Shot in multimillion-dollar Victorian mansion
- Neutral diffuse 3PM lighting
- NEVER include any text or watermarks
```

### Multi-Image Fusion Techniques

**Subject Insertion:**
```
Place the person from the first image into the forest scene, carefully matching the natural lighting and shadows of the environment.
```

**Style Transfer:**
```
Reimagine the first photo in the expressive, swirling style of the second image.
```

**Design Mixing:**
```
Apply the shimmering, colorful pattern of the butterfly wings to the fabric of the dress.
```

### ControlNet-Style Guided Generation
Provide a sketch/wireframe as input, then map elements:
```
Generate characters sitting at a poker table. Map the following to the color-coded poses in the image:
- Green position: Spongebob SquarePants
- Red position: Shadow the Hedgehog
- Blue position: Taylor Swift
```

---

## Quality Boosters

Terms that demonstrably improve output quality:
- `award-winning`
- `Pulitzer Prize winning`
- `professional`
- `highly-detailed`
- `DSLR camera`
- `4K resolution`
- `masterpiece`

---

## Multi-Turn Editing Strategy

### Incremental Building
Focus on one significant change per turn:
1. `Add a floor-to-ceiling bookshelf on the back wall.`
2. `Add this exact sofa, placing it naturally.`
3. `Change walls to sage green, preserving new furniture.`

### Anchor Prompts for Consistency
Combat drift by reinforcing critical elements:
```
Add sunglasses to her face, making sure to keep her facial structure and expression identical to the previous image.
```

### When to Stop
- Limit to 2-3 sequential edits before quality degrades
- Treat upscaling as final step (use external tool)

---

## Troubleshooting Patterns

### Prompt Ignored
1. Simplify to single unambiguous instruction
2. Ensure subject is central, background uncluttered
3. Start new conversation, rephrase with different vocabulary
4. Minor crop/rotation of source can "unstick" the model

### Aspect Ratio Problems
**Frame Hack:** Create blank image in desired ratio (e.g., 1920x1080 white rectangle), upload alongside source, instruct model to work within frame.

### Consistency Loss Over Edits
- Keep source images high-quality with good lighting
- Use anchor phrases reinforcing key features
- Consider regenerating from scratch with consolidated prompt

### Text Rendering Issues
- Be specific: font style, color, size, placement
- For complex text: render externally, provide as input, ask to composite
- Keep text short and simple
