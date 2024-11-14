from io import BytesIO

import requests
from flask import Flask, jsonify, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)


@app.route('/handler', methods=['POST'])
def handler_post():
    body = request.get_json()
    image_url = body.get('image_url')
    headline = body.get('headline')
    author = body.get('author')
    source = body.get('source')

    return process_image(image_url, headline, author, source)


@app.route('/handler', methods=['GET'])
def handler_get():
    image_url = request.args.get('image_url')
    headline = request.args.get('headline')
    author = request.args.get('author')
    source = request.args.get('source')

    if not image_url or not headline or not author or not source:
        return jsonify({"error": "Missing one or more query parameters"}), 400

    return process_image(image_url, headline, author, source)


# Helper function to process the image
def process_image(image_url, headline, author, source):
    try:
        print(f"Fetching image from: {image_url}")
        response = requests.get(image_url)
        response.raise_for_status(
        )  # Raise an error if the HTTP request failed
        img = Image.open(BytesIO(response.content))
        print("Image fetched successfully")

        # Ensure the image is in RGB mode
        if img.mode != 'RGB':
            img = img.convert('RGB')

        draw = ImageDraw.Draw(img)

        # Set up fonts (adjust font sizes for headline and credit text)
        try:
            headline_font = ImageFont.truetype("arial.ttf",
                                               40)  # Headline font size
            credit_font = ImageFont.truetype("arial.ttf",
                                             20)  # Credit font size
        except IOError:
            print("Custom font not available, using default fonts.")
            headline_font = ImageFont.load_default(
            )  # Fallback to default font
            credit_font = ImageFont.load_default()

        # Define positions and sizes for the headline and credit
        img_width, img_height = img.size
        padding = 10

        # Draw headline box
        headline_box_height = 100
        headline_box_y = img_height - headline_box_height

        # Debug: Add detailed print statements to track the error location
        print("Drawing headline box...")
        draw.rectangle([(0, headline_box_y), (img_width, img_height)],
                       fill="white")

        print("Calculating headline text size...")
        text_width, text_height = draw.textsize(headline, font=headline_font)
        headline_position = ((img_width - text_width) // 2, headline_box_y +
                             (headline_box_height - text_height) // 2)

        print(f"Drawing headline at position {headline_position}...")
        draw.text(headline_position,
                  headline,
                  fill="black",
                  font=headline_font)

        # Add author/source credit in the top-right corner
        print("Drawing author/source credit...")
        credit_text = f"Photo: {author} | Source: {source}"
        credit_position = (img_width -
                           draw.textsize(credit_text, font=credit_font)[0] -
                           padding, padding)
        draw.text(credit_position, credit_text, fill="white", font=credit_font)

        # Save to in-memory file
        print("Saving image to buffer...")
        output_buffer = BytesIO()
        img.save(output_buffer, format="JPEG")
        output_buffer.seek(0)

        print("Returning image...")
        # Return the image as a response
        return send_file(output_buffer, mimetype='image/jpeg')

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error fetching image: {str(e)}"}), 400
    except Exception as e:
        print(f"Error during image processing: {str(e)}")
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)