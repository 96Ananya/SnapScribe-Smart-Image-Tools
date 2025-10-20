from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import io
import zipfile
import pytesseract
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_in_prod")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tif', 'tiff', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/split', methods=['POST'])
def split_image():
    # form fields: file, rows, cols
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    try:
        rows = int(request.form.get('rows', 1))
        cols = int(request.form.get('cols', 1))
        if rows <= 0 or cols <= 0:
            raise ValueError
    except:
        flash('Rows and Columns must be positive integers.')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        image = Image.open(file.stream).convert('RGB')
        width, height = image.size
        tile_w = width // cols
        tile_h = height // rows

        # create in-memory zip
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            count = 0
            for r in range(rows):
                for c in range(cols):
                    left = c * tile_w
                    upper = r * tile_h
                    # for last column/row include remainder pixels
                    right = (c + 1) * tile_w if c < cols - 1 else width
                    lower = (r + 1) * tile_h if r < rows - 1 else height
                    box = (left, upper, right, lower)
                    tile = image.crop(box)
                    tile_bytes = io.BytesIO()
                    tile.save(tile_bytes, format='PNG')
                    tile_bytes.seek(0)
                    count += 1
                    zf.writestr(f'{filename.rsplit(".",1)[0]}_r{r+1}_c{c+1}.png', tile_bytes.read())

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{filename.rsplit(".",1)[0]}_split_{rows}x{cols}.zip'
        )
    else:
        flash('Invalid file type. Allowed: png, jpg, jpeg, bmp, tif, tiff, webp')
        return redirect(url_for('index'))


@app.route('/ocr', methods=['POST'])
def ocr():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        img = Image.open(file.stream).convert('RGB')
        # OCR with pytesseract
        try:
            text = pytesseract.image_to_string(img)
        except Exception as e:
            text = ""
            app.logger.error("Tesseract error: %s", e)

        # Provide text result page and a downloadable .txt
        return render_template('index.html', ocr_text=text)
    else:
        flash('Invalid file type. Allowed: png, jpg, jpeg, bmp, tif, tiff, webp')
        return redirect(url_for('index'))


@app.route('/download_text', methods=['POST'])
def download_text():
    content = request.form.get('content', '')
    if content is None:
        content = ''
    bio = io.BytesIO()
    bio.write(content.encode('utf-8'))
    bio.seek(0)
    return send_file(
        bio,
        as_attachment=True,
        download_name='extracted_text.txt',
        mimetype='text/plain'
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Use Flask's dev server locally. In deployment Dockerfile uses gunicorn.
    app.run(host='0.0.0.0', port=port, debug=True)
