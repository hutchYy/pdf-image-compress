import fitz  # PyMuPDF
import io
import sys
from PIL import Image
import pillow_heif

# Register HEIF opener to handle HEIC images
pillow_heif.register_heif_opener()


def compress_pdf_images(input_pdf, output_pdf, quality=50):
    """
    Extract images from a PDF file, compress them, and create a new PDF with the compressed images
    placed on new pages corresponding to their original pages.

    Args:
        input_pdf (str): Path to the input PDF file.
        output_pdf (str): Path to the output PDF file.
        quality (int): JPEG quality for image compression (1-100).
    """
    # Open the input PDF
    input_doc = fitz.open(input_pdf)
    # Create a new PDF for the output
    output_doc = fitz.open()

    # For each page in the input PDF
    for page_num in range(len(input_doc)):
        input_page = input_doc[page_num]
        # Get the page dimensions
        page_rect = input_page.rect
        # Create a new page in the output PDF with the same dimensions
        output_page = output_doc.new_page(
            width=page_rect.width, height=page_rect.height
        )

        # Get the images on the page along with their positions
        image_list = input_page.get_images(full=True)
        images_info = []
        if image_list:
            # For each image on the page
            for img_index, img in enumerate(image_list):
                xref = img[0]
                # Extract the image bytes
                base_image = input_doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Open the image with PIL
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                except Exception as e:
                    print(f"Could not open image xref {xref}: {e}")
                    continue

                # Convert image to RGB if necessary
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")

                # Compress the image
                output_buffer = io.BytesIO()
                image.save(output_buffer, format="JPEG", quality=quality)
                compressed_image_bytes = output_buffer.getvalue()

                # Attempt to get the image's position on the page
                # This requires parsing the page content
                # Note: This method may not be accurate for all PDFs
                image_rects = []
                for img_info in input_page.get_images():
                    if img_info[0] == xref:
                        # Placeholder for position; PyMuPDF does not provide positions directly
                        # You can place images at (0, 0) or any default position
                        # Alternatively, you can try to parse the content stream to find positions
                        # For simplicity, we'll place images at the top-left corner
                        image_rects.append(fitz.Rect(0, 0, image.width, image.height))

                # Insert the compressed image into the output page
                for rect in image_rects:
                    output_page.insert_image(rect, stream=compressed_image_bytes)

    # Save the output PDF
    output_doc.save(output_pdf)
    input_doc.close()
    output_doc.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compress_pdf_images.py input.pdf output.pdf")
        sys.exit(1)
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    compress_pdf_images(input_pdf, output_pdf)
