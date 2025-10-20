from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
from PIL import Image
import zipfile
import io
import easyocr
import numpy as np
from collections import Counter

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# ========== OPTION 1: IMAGE SPLITTER ==========
@app.route('/split', methods=['POST'])
def split_image():
    try:
        file = request.files['image']
        rows = int(request.form['rows'])
        cols = int(request.form['cols'])

        img = Image.open(file)
        img_width, img_height = img.size
        tile_width = img_width // cols
        tile_height = img_height // rows

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for r in range(rows):
                for c in range(cols):
                    left = c * tile_width
                    top = r * tile_height
                    right = (c + 1) * tile_width
                    bottom = (r + 1) * tile_height
                    box = (left, top, right, bottom)
                    tile = img.crop(box)
                    img_bytes = io.BytesIO()
                    tile.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    zip_file.writestr(f'slice_{r+1}_{c+1}.png', img_bytes.read())

        zip_buffer.seek(0)
        return send_file(zip_buffer, as_attachment=True, download_name='slices.zip')
    except Exception as e:
        flash(f"Error splitting image: {e}")
        return redirect(url_for('index'))


# ========== OPTION 2: IMAGE TO TEXT (OCR) ==========
@app.route('/extract_text', methods=['POST'])
def extract_text():
    try:
        file = request.files['image']
        reader = easyocr.Reader(['en'])
        result = reader.readtext(np.array(Image.open(file)))

        extracted_text = "\n".join([res[1] for res in result])
        return render_template('index.html', extracted_text=extracted_text)
    except Exception as e:
        flash(f"Error extracting text: {e}")
        return redirect(url_for('index'))


# ========== OPTION 3: COLOR PALETTE EXTRACTOR ==========
# ========== OPTION 3: COLOR PALETTE EXTRACTOR ==========
@app.route('/extract_palette', methods=['POST'])
def extract_palette():
    try:
        file = request.files['image']
        num_colors = int(request.form.get('num_colors', 5))

        img = Image.open(file).convert('RGB')
        img = img.resize((150, 150))
        pixels = np.array(img).reshape(-1, 3)

        # Count most common colors
        counter = Counter(map(tuple, pixels))
        most_common = counter.most_common(num_colors)

        # Convert np.uint8 values to normal integers for clean display
        colors = [f"rgb({int(r)}, {int(g)}, {int(b)})" for (r, g, b), _ in most_common]

        return render_template('index.html', colors=colors)
    except Exception as e:
        flash(f"Error extracting color palette: {e}")
        return redirect(url_for('index'))


# ========== OPTION 4: IMAGE RESIZER ==========
@app.route('/resize_image', methods=['POST'])
def resize_image():
    try:
        file = request.files['image']
        width = int(request.form['width'])
        height = int(request.form['height'])

        img = Image.open(file)
        resized_img = img.resize((width, height))
        img_bytes = io.BytesIO()
        resized_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return send_file(img_bytes, as_attachment=True, download_name='resized_image.png')
    except Exception as e:
        flash(f"Error resizing image: {e}")
        return redirect(url_for('index'))


# ========== HOME ROUTE ==========
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
