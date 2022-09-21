import cv2
import pytesseract
import re as re
import json
from flask import Flask

app = Flask(__name__)

# Draw a box around each sentence and show the image
def box(pro_img):
    custom_config = r' -c tessedit_char_whitelist="HBECO0123456789 " --psm 3'  # Config for tesseract
    d = pytesseract.image_to_data(pro_img, output_type=pytesseract.Output.DICT, config=custom_config)
    pattern = r"HBE\d{5}\d{3}[O|B|C]\d{2}$"

    # Remove all empty strings the OCR interpreted lables / text cleaning
    d['text'] = [x.strip(' ') for x in d['text']]
    n_boxes = len(d['text'])
    words = []
    for i in range(n_boxes):
        if len(d['text'][i]) > 1:
            words.append(i)

    # Iterate on the text and draw boxes where the pattern is found
    found = []
    for i in words:
        try:
            # Looks at each word and the five next words to see if it matches the pattern
            if re.match(pattern, d['text'][i] + d['text'][words[words.index(i)+1]] + d['text'][words[words.index(i)+2]] + d['text'][words[words.index(i)+3]]):
                found.append([d['text'][i] + d['text'][words[words.index(i)+1]] + d['text'][words[words.index(i)+2]] + d['text'][words[words.index(i)+3]], d['left'][i], d['top'][i], d['width'][i], d['height'][i]])
        except IndexError:
            pass

    return json.dumps(found)


# This function pre-processes the images
def pre_process(img):
    # Convert image to greyscale
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Binarize the image with a threshold function making the pixels either black or white
    _, img_thres = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Noice removal and contour filtering using a mask
    cnts = cv2.findContours(img_thres, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    mask = img_thres.copy()
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        if cv2.contourArea(c) < 100000:
            cv2.drawContours(mask, [c], -1, (0, 0, 0), -1)
    mask = 255 - mask
    img_pros = cv2.bitwise_and(img_thres, img_thres, mask=mask)
    img_pros = 255 - img_pros

    # Apply blur to smoothen the image and remove noise
    img_pros = cv2.GaussianBlur(img_pros, (5, 5), 0)

    return img_pros

@app.route("/<input>")

def process(input):
    img = cv2.imread("Python/Images/IMG_0894.jpg") # TODO Temp
    #img = cv2.imread(input) # TODO Temp
    # Rescale to 300DPI #TODO adjust for final camera setup
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    pro_img = pre_process(img)
    return box(pro_img)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
