
"""NeuroLens Cute Studio — Six working photo filters."""

import io
import random

import streamlit as st
from PIL import (
    Image,
    ImageEnhance,
    ImageFilter,
    ImageDraw,
    ImageFont,
    ImageOps,
)


FILTERS = [
    "Lavender Sparkle",
    "Cute Cat",
    "Butterfly Dream",
    "Clean Portrait",
    "Blue Cyber",
    "Cinematic Vintage",
]


def lavender_filter(image):
    image = ImageEnhance.Color(image).enhance(1.15)
    image = ImageEnhance.Brightness(image).enhance(1.07)

    glow = image.filter(ImageFilter.GaussianBlur(14))
    image = Image.blend(image, glow, 0.18)

    overlay = Image.new("RGB", image.size, (190, 155, 235))
    image = Image.blend(image, overlay, 0.13)

    return image


def cat_filter(image):
    image = ImageEnhance.Color(image).enhance(1.2)
    image = ImageEnhance.Brightness(image).enhance(1.05)
    return image


def butterfly_filter(image):
    image = ImageEnhance.Color(image).enhance(1.25)
    image = ImageEnhance.Brightness(image).enhance(1.08)

    overlay = Image.new("RGB", image.size, (255, 205, 230))
    return Image.blend(image, overlay, 0.12)


def clean_portrait(image):
    soft = image.filter(ImageFilter.GaussianBlur(1.2))
    image = Image.blend(image, soft, 0.12)
    image = ImageEnhance.Color(image).enhance(1.08)
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = ImageEnhance.Sharpness(image).enhance(1.15)
    return image


def blue_cyber(image):
    image = ImageEnhance.Contrast(image).enhance(1.2)
    image = ImageEnhance.Color(image).enhance(1.35)

    overlay = Image.new("RGB", image.size, (20, 95, 210))
    image = Image.blend(image, overlay, 0.28)

    return image


def cinematic_vintage(image):
    image = ImageOps.grayscale(image).convert("RGB")
    image = ImageEnhance.Contrast(image).enhance(1.15)

    warm = Image.new("RGB", image.size, (220, 160, 105))
    image = Image.blend(image, warm, 0.35)

    return image


def apply_filter(image, filter_name):
    image = image.convert("RGB")

    functions = {
        "Lavender Sparkle": lavender_filter,
        "Cute Cat": cat_filter,
        "Butterfly Dream": butterfly_filter,
        "Clean Portrait": clean_portrait,
        "Blue Cyber": blue_cyber,
        "Cinematic Vintage": cinematic_vintage,
    }

    return functions[filter_name](image)


def draw_cat_ears(image):
    image = image.convert("RGBA")
    width, height = image.size

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    points_left = [
        (int(width * .20), int(height * .28)),
        (int(width * .28), int(height * .05)),
        (int(width * .39), int(height * .29)),
    ]

    points_right = [
        (int(width * .61), int(height * .29)),
        (int(width * .72), int(height * .05)),
        (int(width * .80), int(height * .28)),
    ]

    draw.polygon(points_left, fill=(65, 45, 70, 220))
    draw.polygon(points_right, fill=(65, 45, 70, 220))

    draw.polygon(
        [
            (int(width * .25), int(height * .24)),
            (int(width * .29), int(height * .12)),
            (int(width * .35), int(height * .25)),
        ],
        fill=(255, 160, 195, 230),
    )

    draw.polygon(
        [
            (int(width * .65), int(height * .25)),
            (int(width * .71), int(height * .12)),
            (int(width * .75), int(height * .24)),
        ],
        fill=(255, 160, 195, 230),
    )

    return Image.alpha_composite(image, overlay)


def draw_butterflies(image):
    image = image.convert("RGBA")
    width, height = image.size

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    positions = [
        (int(width * .15), int(height * .20)),
        (int(width * .82), int(height * .18)),
        (int(width * .78), int(height * .75)),
        (int(width * .17), int(height * .80)),
    ]

    for x, y in positions:
        radius = max(5, width // 45)

        draw.ellipse(
            (x - radius, y - radius, x, y + radius),
            fill=(225, 145, 255, 210),
        )

        draw.ellipse(
            (x, y - radius, x + radius, y + radius),
            fill=(255, 170, 215, 210),
        )

        draw.line(
            (x, y - radius, x, y + radius),
            fill=(90, 55, 130, 230),
            width=max(1, width // 400),
        )

    return Image.alpha_composite(image, overlay)


def draw_sparkles(image):
    image = image.convert("RGBA")
    width, height = image.size

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for _ in range(35):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        size = max(2, width // 180)

        draw.line(
            (x - size, y, x + size, y),
            fill=(255, 255, 235, 210),
            width=2,
        )

        draw.line(
            (x, y - size, x, y + size),
            fill=(255, 255, 235, 210),
            width=2,
        )

    return Image.alpha_composite(image, overlay)


def add_text(image, text):
    image = image.convert("RGBA")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(
            "DejaVuSans.ttf",
            max(18, image.width // 22),
        )
    except OSError:
        font = ImageFont.load_default()

    draw.text(
        (20, image.height - 55),
        text,
        fill=(255, 255, 255, 240),
        font=font,
        stroke_width=2,
        stroke_fill=(40, 30, 50, 180),
    )

    return image


def to_png_bytes(image):
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def create_sticker(sticker_name):
    size = 600
    sticker = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sticker)

    if sticker_name == "Cat Ears":
        draw.polygon(
            [(100, 300), (175, 50), (290, 285)],
            fill=(70, 50, 80, 255),
        )
        draw.polygon(
            [(310, 285), (425, 50), (500, 300)],
            fill=(70, 50, 80, 255),
        )
        draw.polygon(
            [(150, 260), (180, 110), (245, 260)],
            fill=(255, 160, 195, 255),
        )
        draw.polygon(
            [(355, 260), (420, 110), (455, 260)],
            fill=(255, 160, 195, 255),
        )

    else:
        draw.ellipse(
            (110, 180, 300, 390),
            fill=(210, 145, 255, 220),
        )
        draw.ellipse(
            (300, 180, 490, 390),
            fill=(255, 155, 205, 220),
        )
        draw.ellipse(
            (110, 300, 300, 500),
            fill=(255, 175, 225, 220),
        )
        draw.ellipse(
            (300, 300, 490, 500),
            fill=(210, 155, 255, 220),
        )
        draw.line(
            (300, 190, 300, 470),
            fill=(90, 60, 120, 255),
            width=8,
        )

    return sticker


def render(st):
    st.title("📸 NeuroLens Cute Studio")

    st.write(
        "Upload a photo, explore six creative filters, "
        "add effects and export your edited image."
    )

    uploaded = st.file_uploader(
        "Choose a photo",
        type=["jpg", "jpeg", "png", "webp"],
        key="nl_photo_upload",
    )

    if uploaded is None:
        st.info("Upload a photo to start your studio.")
    else:
        try:
            original = Image.open(uploaded)
            original = ImageOps.exif_transpose(original).convert("RGB")

            max_dimension = 1800
            original.thumbnail(
                (max_dimension, max_dimension)
            )

            st.subheader("Choose your filter")

            filter_name = st.selectbox(
                "Six photo filters",
                FILTERS,
                key="nl_photo_filter",
            )

            edited = apply_filter(original, filter_name)

            if filter_name == "Cute Cat":
                edited = draw_cat_ears(edited)

            if filter_name == "Butterfly Dream":
                edited = draw_butterflies(edited)

            if filter_name == "Lavender Sparkle":
                edited = draw_sparkles(edited)

            st.subheader("Adjust your photo")

            brightness = st.slider(
                "Brightness",
                0.5,
                1.8,
                1.0,
                0.05,
            )

            contrast = st.slider(
                "Contrast",
                0.5,
                1.8,
                1.0,
                0.05,
            )

            edited = ImageEnhance.Brightness(
                edited.convert("RGB")
            ).enhance(brightness)

            edited = ImageEnhance.Contrast(
                edited
            ).enhance(contrast)

            st.subheader("Add your own text")

            caption = st.text_input(
                "Photo caption (optional)",
                max_chars=80,
            )

            if caption.strip():
                edited = add_text(edited, caption.strip())

            left, right = st.columns(2)

            with left:
                st.markdown("**Before**")
                st.image(original, use_container_width=True)

            with right:
                st.markdown("**After**")
                st.image(edited, use_container_width=True)

            st.download_button(
                "⬇️ Download edited photo",
                data=to_png_bytes(edited),
                file_name="neurolens_edited.png",
                mime="image/png",
                use_container_width=True,
            )

            st.divider()
            st.subheader("✨ Sticker Maker")

            sticker_name = st.selectbox(
                "Choose a transparent sticker",
                ["Cat Ears", "Butterfly"],
            )

            sticker = create_sticker(sticker_name)

            st.image(
                sticker,
                caption="Transparent PNG sticker",
                width=180,
            )

            st.download_button(
                "Download transparent sticker",
                data=to_png_bytes(sticker),
                file_name="neurolens_sticker.png",
                mime="image/png",
            )

        except Exception:
            st.error(
                "This photo could not be processed. "
                "Try another JPG or PNG image."
            )

    st.divider()

    st.caption(
        "Photo processing happens within the Streamlit app. "
        "These effects do not identify personality, diagnose emotions "
        "or determine psychological traits from facial appearance. "
        "Automatic background removal and advanced face tracking "
        "are planned separately."
    )
