from flask import Flask, Response, render_template, jsonify
import os
import time
from mimetypes import guess_type
import pypdfium2 as pdfium

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_PATH,'static','images')

app = Flask(__name__)

def is_image(file:str)->bool:
    imagetypes = ['jpg','jpeg','png', 'pdf']
    for t in imagetypes:
        if file.endswith(t):
            return True 
    return False

def is_pdf(file:str)->bool:
    imagetypes = ['pdf']
    for t in imagetypes:
        if file.endswith(t):
            return True 
    return False

def convert_pdf_to_img(file):
    #file = os.path.join(IMAGE_PATH,file)
    pdf = pdfium.PdfDocument(file)
    #path, filename_ext = os.path.split(file)
    path, ext = os.path.splitext(file)
    path_png = path+'.png'
    n_pages = len(pdf)
    if n_pages > 0:
        page = pdf[0]
        pil_image = page.render(
            pdfium.PdfBitmap.to_pil,
            optimize_mode="lcd",
        )
        pil_image.save(path_png)
        return path_png

def get_logo():
    logo_images = os.path.join(BASE_PATH,'static','logo')
    images = get_all_images(logo_images)
    if images:
        path_to_image = os.path.join(logo_images, images[0])
        if os.path.exists(str(path_to_image)):
            return path_to_image

def gen():
    i = 0
    while True:
        try:
            images = get_all_images()
            if not images and get_logo():
                images.append(get_logo())

            if images:
                image_name = images[i]
                path_to_image = os.path.join(IMAGE_PATH,image_name)
                if os.path.exists(path_to_image):
                    if is_pdf(path_to_image):
                        path_to_image = convert_pdf_to_img(path_to_image)
                
                    if os.path.exists(str(path_to_image)):
                        im = open(path_to_image, 'rb').read()
                        (mt, encoding )=guess_type(path_to_image)
                        mt_bytes = bytes(mt, 'raw_unicode_escape')
  
                        yield (b'--frame\r\n'
                            b'Content-Type:'+ mt_bytes +b'\r\n\r\n' + im + b'\r\n')
                        time_next:str =  str(os.getenv('TIME_NEXT','30'))
                        if time_next.isdigit():
                            time_next:int = int(time_next)
                        else:
                            time_next:int = 30
                        print('Wait', str(time_next))
                        time.sleep(time_next)
        except Exception as e:
            print(e)
            t = e
        finally:
            i += 1
            if i >= len(images):
                i = 0
        


def get_all_images(path:str=IMAGE_PATH):
    #for img in os.listdir(IMAGE_PATH):
    #    if is_pdf(img):
    #        convert_pdf_to_img(img)
    images = [img for img in os.listdir(path) if is_image(img) ]
    return images


@app.route('/slideshow')
def slideshow():
    return Response(gen(),mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    images = [img for img in os.listdir(IMAGE_PATH) if is_image(img) ]
    return render_template('main.html')


@app.route('/images')
def get_image_list():
    images = get_all_images()
    return jsonify(images)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug= bool(os.environ.get('DEBUG', False))
    app.run(host='0.0.0.0', port=port, debug=debug)
