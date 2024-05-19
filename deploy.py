import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from deoldify import device
from deoldify.device_id import DeviceId
from deoldify.visualize import get_image_colorizer
from transformers import pipeline
import tempfile
import os
import warnings
from UtilityFunctions import *

warnings.filterwarnings("ignore", category=UserWarning, message=".*Your .* set is empty.*")
device.set(device=DeviceId.GPU0)

# Initialize DeOldify colorizer
colorizer = get_image_colorizer(artistic=True)

# Initialize image captioning pipeline
captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")

# Main Streamlit app code

# Define the main function
def main():
    # Custom CSS for styling
    st.markdown("""
        <style>
        .title {
            font-size: 48px;
            font-weight: bold;
            color: #FF6347;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            font-size: 20px;
            border-radius: 12px;
            padding: 10px 20px;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .file-uploader {
            text-align: center;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .tabs {
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title with custom style
    st.markdown('<h1 class="title">Necromancer App</h1>', unsafe_allow_html=True)

    # Create tabs for "Image" and "Video"
    tabs = st.tabs(["📷 Image", "🎥 Video"])

    with tabs[0]:
        st.markdown('<div class="file-uploader">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_file is not None:
            # Display uploaded image
            st.image(uploaded_file, caption='Uploaded Image.', use_column_width=True)

            # Convert uploaded file to PIL Image
            img_pil = Image.open(uploaded_file)

            # Save PIL Image to a temporary file with explicit extension
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            img_pil.save(temp_file.name)
            temp_file.close()

            # Colorize the image using DeOldify (colorizer not defined here)
            img_colorized = colorizer.get_transformed_image(path=temp_file.name, render_factor=35, watermarked=False)

            # Get caption for the image (captioner not defined here)
            caption = captioner(img_pil)

            # Add caption to the image with black background
            draw = ImageDraw.Draw(img_colorized)
            text = caption[0]["generated_text"]
            font = ImageFont.truetype('arial.ttf', size=50)
            text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
            image_width, image_height = img_colorized.size
            text_x = (image_width - text_width) // 2
            text_y = image_height - text_height - 20

            # Calculate background rectangle dimensions
            bg_left = text_x - 10
            bg_top = text_y - 10
            bg_right = text_x + text_width + 10
            bg_bottom = text_y + text_height + 10

            # Draw filled black rectangle for background
            draw.rectangle([bg_left, bg_top, bg_right, bg_bottom], fill='black')

            # Add text to the image
            draw.text((text_x, text_y), text, font=font, fill='white')

            # Display the colorized and captioned image
            st.image(img_colorized, caption='Colorized and Captioned Image.', use_column_width=True)

    with tabs[1]:
        st.markdown('<div class="file-uploader">', unsafe_allow_html=True)
        uploaded_video = st.file_uploader("Choose a video...", type=["mp4", "avi", "mov"])
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_video is not None:
            # Save uploaded video to a temporary file
            temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_video.write(uploaded_video.read())
            temp_video.close()

            # Perform video colorization and captioning (colorize_video not defined here)
            output_path = tempfile.mkdtemp()
            colorize_video(colorizer, captioner, temp_video.name, output_path=output_path)

            # Display the colorized and captioned video
            output_video_path = os.path.join(output_path, 'output.mp4')
            st.video(output_video_path)

if __name__ == '__main__':
    main()

# def main():
    
#     st.title("Necromancer App")
#     option = st.selectbox("Choose an option:", ("Image", "Video"))

#     if option == "Image":
#         uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

#         if uploaded_file is not None:
#             # Display uploaded image
#             st.image(uploaded_file, caption='Uploaded Image.', use_column_width=True)

#             # Convert uploaded file to PIL Image
#             img_pil = Image.open(uploaded_file)

#             # Save PIL Image to a temporary file with explicit extension
#             temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
#             img_pil.save(temp_file.name)
#             temp_file.close()

#             # Colorize the image using DeOldify
#             img_colorized = colorizer.get_transformed_image(path=temp_file.name, render_factor=35, watermarked=False)

#             # Get caption for the image
#             caption = captioner(img_pil)

#             # Add caption to the image with black background
#             draw = ImageDraw.Draw(img_colorized)
#             text = caption[0]["generated_text"]
#             font = ImageFont.truetype('arial.ttf', size=50)
#             text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
#             image_width, image_height = img_colorized.size
#             text_x = (image_width - text_width) // 2
#             text_y = image_height - text_height - 20

#             # Calculate background rectangle dimensions
#             bg_left = text_x - 10
#             bg_top = text_y - 10
#             bg_right = text_x + text_width + 10
#             bg_bottom = text_y + text_height + 10

#             # Draw filled black rectangle for background
#             draw.rectangle([bg_left, bg_top, bg_right, bg_bottom], fill='black')

#             # Add text to the image
#             draw.text((text_x, text_y), text, font=font, fill='white')

#             # Display the colorized and captioned image
#             st.image(img_colorized, caption='Colorized and Captioned Image.', use_column_width=True)

#     elif option == "Video":
#         uploaded_video = st.file_uploader("Choose a video...", type=["mp4", "avi", "mov"])

#         if uploaded_video is not None:
#             # Save uploaded video to a temporary file
#             temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
#             temp_video.write(uploaded_video.read())
#             temp_video.close()

#             # Perform video colorization and captioning
#             output_path = tempfile.mkdtemp()
#             colorize_video(colorizer, captioner, temp_video.name, output_path=output_path)

#             # Display the colorized and captioned video
#             output_video_path = os.path.join(output_path, 'output.mp4')
#             st.video(output_video_path)

# if __name__ == '__main__':
#     main()

