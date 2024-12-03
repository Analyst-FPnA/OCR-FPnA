import pytesseract
from PIL import Image

# Specify the path to the Tesseract executable if it's not in your PATH
# For example, on Windows, it might look like this:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def read_text_from_image(image_path):
    # Open the image using Pillow
    image = Image.open(image_path)
    
    # Use pytesseract to do OCR on the image
    text = pytesseract.image_to_string(image)
    
    return text

if __name__ == "__main__":
    # Path to your image file
    image_path = 'images/TesBack.jpg'
    
    # Read text from the image
    extracted_text = read_text_from_image(image_path)
    
    # Print the extracted text
    print("Extracted Text:")
    print(extracted_text)