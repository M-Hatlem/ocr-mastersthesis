import cv2
import pytesseract
import re as re
import json
import numpy as np
from flask import Flask

app = Flask(__name__)




#TODO  FOR TESTING
def ResizeWithAspectRatio(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv2.resize(image, dim, interpolation=inter)
#TODO END OF TEST CODE


# Draw a box around each sentence and show the image
def box(pro_images):
    #TODO HAVE A LOOK AT 2nd for loop to see if it can be moved out of the first or improved

    # loops through all images and applies OCR
    complete = []
    partial = []
    custom_config = r' -c tessedit_char_whitelist="HBECO0123456789 " --psm 3'  # Config for tesseract
    for img in pro_images:
        d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config)

        # Remove all empty strings the OCR interpreted lables / text cleaning
        d['text'] = [x.strip(' ') for x in d['text']]
        n_boxes = len(d['text'])
        words = []
        for i in range(n_boxes):
            if len(d['text'][i]) > 1:
                words.append(i)

        # Iterate on the text and draw boxes where the pattern is found
        for i in words:
            try:
                # Looks at each word and the five next words to see if it matches the pattern
                pattern_1 = re.match(r"HBE", d['text'][i])
                pattern_2 = re.match(r"^\d{5}$", d['text'][words[words.index(i)+1]])
                pattern_3 = re.match(r"^\d{3}$", d['text'][words[words.index(i)+2]])
                pattern_4 = re.match(r"^[O|B|C]\d{2}$", d['text'][words[words.index(i)+3]])
                if [pattern_1, pattern_2, pattern_3, pattern_4].count(None) == 0: # If all patterns match correctly then the line is identified
                    # patters is listed as [STRING WITH CODE, LEFT, TOP, WIDTH, HEIGHT] Width and Height are addtionally calulated to include the length of the entire casette
                    # top and left is pixel coordinates. Width and height is the legnth of the words in pixels
                    complete.append({
                        "id": d['text'][words[words.index(i)+1]] + "-" + d['text'][words[words.index(i)+2]] + "-" + d['text'][words[words.index(i)+3]],
                        "left": d['left'][i],
                        "top": d['top'][i],
                        "width": d['left'][i+1] + d['width'][i+1] - d['left'][i],
                        "height": d['top'][i+2] + d['height'][i+2] - d['top'][i]})

                elif [pattern_1, pattern_2, pattern_3, pattern_4].count(None) == 1:  # If only 3 patterns match correctly then the line is partly identified
                    if pattern_1 is None:
                        # pattern 1 can be added to complete as hbe is mainly used for coordinates
                        complete.append({
                            "id": d['text'][words[words.index(i) + 1]] + "-" + d['text'][words[words.index(i) + 2]] + "-" + d['text'][words[words.index(i) + 3]],
                            "left": d['left'][i+1],
                            "top": d['top'][i+1],
                            "width": d['width'][i+1],
                            "height": d['height'][i+1] * 2})
                    elif pattern_2 is None:
                        partial.append({
                            "id": "NONE" + "-" + d['text'][words[words.index(i) + 2]] + "-" + d['text'][words[words.index(i) + 3]],
                            "left":   d['left'][i],
                            "top": d['top'][i],
                            "width": d['left'][i+2] + d['width'][i+2] - d['left'][i],
                            "height": d['top'][i+2] + d['height'][i+2] - d['top'][i]})
                    elif pattern_3 is None:
                        partial.append({
                            "id": d['text'][words[words.index(i) + 1]] + "-" + "NONE" + "-" + d['text'][words[words.index(i) + 3]],
                            "left":   d['left'][i],
                            "top": d['top'][i],
                            "width": d['left'][i+1] + d['width'][i+1] - d['left'][i],
                            "height": d['top'][i+3] + d['height'][i+3] - d['top'][i]})
                    elif pattern_4 is None:
                        partial.append({
                            "id": d['text'][words[words.index(i) + 1]] + "-" + d['text'][words[words.index(i) + 2]] + "-" + "NONE",
                            "left":   d['left'][i],
                            "top": d['top'][i],
                            "width": d['left'][i+1] + d['width'][i+1] - d['left'][i],
                            "height": d['top'][i+2] + d['height'][i+2] - d['top'][i]})
            except IndexError:
                pass

    # TODO DRAW ON IMGAGE FOR TEST
    pro_resize = ResizeWithAspectRatio(img, height=1080)
    cv2.imshow('pro_resize', pro_resize)
    cv2.waitKey(0)
    # TODO END OF TEST CODE
    return json.dumps([complete, partial])


# This function pre-processes the images
def pre_process(img):
    # Convert image to greyscale blur and sharpen to enhance edges for edge detection
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #img_blur = cv2.medianBlur(img_gray, 11)
    img_blur = cv2.bilateralFilter(img_gray, 21, 75, 75)
    #img_blur = cv2.GaussianBlur(img_gray, (7, 7), 11)
    sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    img_sharpen = cv2.filter2D(img_blur, -1, sharpen_kernel)

    # Binarize the image with a threshold function making the pixels either black or white, then morph to remove noise
    img_thres = cv2.adaptiveThreshold(img_sharpen, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,111,2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    img_close = cv2.morphologyEx(img_thres, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Find contours and filter using threshold area
    cnts = cv2.findContours(img_close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    # Find rectangles, ignore the ones smaller than 50000 pixels and larger than 200000 px
    img_numb = 0

    for c in cnts:
        area = cv2.contourArea(c)
        if area > 50000 and area < 200000:
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(img, (x, y), (x + w, y + h), (36, 255, 12), 2)
            img_numb+=1


    print(img_numb)
    #TODO SPLIT EACH RECT COORDINATES INTO IMAGES FROM IMG_GRAY
    #TODO PROCESS EACH SPLIT IMG WIHT PROCESS IMG PART AND ADD TO LIST
    #TODO OPTIONAL: IF TOO MANY RECTANGLES DETECTD, SORT BY SIZE AND REMOVE THE ONES THAT ARE LESS THAN 90% THE SIZE OF THE ONE WE
    #return [img]
    return [img_close]
    # Return a list of all images


def process_image_part(img_gray):
    img_thres = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # Noise removal and contour filtering using a mask
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

    return mask
    #IMPLEMANT RECTANLGE DETECTION INSTEAD OF MASK, THEN PROCESS EACH RECTANGLE FOR TEXT

    # RECTANGLE DETECTION AND OCR SHOULD BE DONE ON 2 DIFFERENT IMAGES
    # USE ADAPTIVE THRESHOLDING TO SPLIT IMAGES AND RECOGNISE RECTNAGLES
    # THEN COPY THEM OUT OF GREYSCALE AND USE OTSU ON EACH INDIDUALLY BEFORE OCR


@app.route('/api/image/<path:url>',)
def process(url):
    img = cv2.imread(url)
    # Rescale to 300DPI #TODO adjust for final camera setup
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    pro_images = pre_process(img)
    return box(pro_images)



if __name__ == "__main__":
    #TODO REMOVED WHEN TESTING
    #   app.run(host='127.0.0.1', port=5000)


    #TODO  FOR TESTING
    i = process("Images\samsung s20\\20221128_132802.jpg")
    #i = process("Images\iphone 13\IMG_0894.jpg")
    print(i)
    #TODO END OF TEST CODE

