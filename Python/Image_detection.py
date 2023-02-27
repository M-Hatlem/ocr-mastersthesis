import cv2
import pytesseract
import re as re
import json
import numpy as np
from flask import Flask
import sys

app = Flask(__name__)

# rezise image for showing in tests
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
# To call:
# cv2.imshow('pro_resize', ResizeWithAspectRatio(img, height=1080, width=720))
# cv2.waitKey(0)
# to print with flask     print('Hello world!', file=sys.stderr)


# Draw a box around each sentence and show the image
def find_box(pro_images):
    #TODO DEAL WITH POSSIBLE DUPLICATES IN JSON OUTPUT FILE

    # loops through all images and applies OCR
    complete = []
    partial = []
    custom_config = r' -c tessedit_char_whitelist="HBECO0123456789 " --psm 3'  # Config for tesseract
    for j in range(len(pro_images)):
        img = pro_images[j]["image_data"]
        t_output = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config)

        # TODO TESTING
        #cv2.imshow('pro_resize', ResizeWithAspectRatio(img, height=1080, width=720))
        #cv2.waitKey(0)
        # TODO TESTING END

        # Remove all empty strings the OCR interpreted lables / text cleaning
        t_output['text'] = [x.strip(' ') for x in t_output['text']]
        number_of_boxes = len(t_output['text'])
        words = []

        for i in range(number_of_boxes):
            if len(t_output['text'][i]) > 1:
                words.append(i)

        # Iterate on the text and draw boxes where the pattern is found
        for i in words:
            try:
                # Looks at each word and the five next words to see if it matches the pattern
                pattern_1 = re.match(r"HBE", t_output['text'][i])
                pattern_2 = re.match(r"^\d{5}$", t_output['text'][words[words.index(i)+1]])
                pattern_3 = re.match(r"^\d{3}$", t_output['text'][words[words.index(i)+2]])
                pattern_4 = re.match(r"^[O|B|C]\d{2}$", t_output['text'][words[words.index(i)+3]])
                if [pattern_1, pattern_2, pattern_3, pattern_4].count(None) == 0: # If all patterns match correctly then the line is identified
                    # patters is listed as [STRING WITH CODE, LEFT, TOP, WIDTH, HEIGHT] Width and Height are addtionally calulated to include the length of the entire casette
                    # top and left is pixel coordinates. Width and height is the legnth of the words in pixels
                    complete.append({
                        "id": t_output['text'][words[words.index(i)+1]] + "-" + t_output['text'][words[words.index(i)+2]] + "-" + t_output['text'][words[words.index(i)+3]],
                        "left": t_output['left'][i] + pro_images[j]["x"],
                        "top": t_output['top'][i] + pro_images[j]["y"],
                        "width": t_output['left'][i+1] + t_output['width'][i+1] - t_output['left'][i],
                        "height": t_output['top'][i+2] + t_output['height'][i+2] - t_output['top'][i]}
                    )

                elif [pattern_1, pattern_2, pattern_3, pattern_4].count(None) == 1:  # If only 3 patterns match correctly then the line is partly identified
                    if pattern_1 is None:
                        # pattern 1 can be added to complete as hbe is mainly used for coordinates
                        complete.append({
                            "id": t_output['text'][words[words.index(i) + 1]] + "-" + t_output['text'][words[words.index(i) + 2]] + "-" + t_output['text'][words[words.index(i) + 3]],
                            "left": t_output['left'][i+1] + pro_images[j]["x"],
                            "top": t_output['top'][i+1] + pro_images[j]["y"],
                            "width": t_output['width'][i+1],
                            "height": t_output['height'][i+1] * 2})
                    elif pattern_2 is None:
                        partial.append({
                            "id": "NONE" + "-" + t_output['text'][words[words.index(i) + 2]] + "-" + t_output['text'][words[words.index(i) + 3]],
                            "left":   t_output['left'][i] + pro_images[j]["x"],
                            "top": t_output['top'][i] + pro_images[j]["y"],
                            "width": t_output['left'][i+2] + t_output['width'][i+2] - t_output['left'][i],
                            "height": t_output['top'][i+2] + t_output['height'][i+2] - t_output['top'][i]})
                    elif pattern_3 is None:
                        partial.append({
                            "id": t_output['text'][words[words.index(i) + 1]] + "-" + "NONE" + "-" + t_output['text'][words[words.index(i) + 3]],
                            "left":   t_output['left'][i] + pro_images[j]["x"],
                            "top": t_output['top'][i] + pro_images[j]["y"],
                            "width": t_output['left'][i+1] + t_output['width'][i+1] - t_output['left'][i],
                            "height": t_output['top'][i+3] + t_output['height'][i+3] - t_output['top'][i]})
                    elif pattern_4 is None:
                        partial.append({
                            "id": t_output['text'][words[words.index(i) + 1]] + "-" + t_output['text'][words[words.index(i) + 2]] + "-" + "NONE",
                            "left":   t_output['left'][i] + pro_images[j]["x"],
                            "top": t_output['top'][i] + pro_images[j]["y"],
                            "width": t_output['left'][i+1] + t_output['width'][i+1] - t_output['left'][i],
                            "height": t_output['top'][i+2] + t_output['height'][i+2] - t_output['top'][i]})
            except IndexError:
                pass
    return json.dumps([complete, partial])


# This function pre-processes the images
def pre_process(img):
    #TODO IMPROVE THE DETECTION HERE

    # Convert image to greyscale blur and sharpen to enhance edges for edge detection
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #img_blur = cv2.medianBlur(img_gray, 11)
    img_blur = cv2.bilateralFilter(img_gray, 21, 75, 75)
    #img_blur = cv2.GaussianBlur(img_gray, (7, 7), 11)
    sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    img_sharpen = cv2.filter2D(img_blur, -1, sharpen_kernel)

    # Binarize the image with a threshold function making the pixels either black or white
    img_thres = cv2.adaptiveThreshold(img_sharpen, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,111,2)

    # Erode to expand background and define background better
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    img_erode = cv2.erode(img_thres, kernel, iterations=1)

    # Close to remove noise
    img_close = cv2.morphologyEx(img_erode, cv2.MORPH_CLOSE, kernel, iterations=1)

    img_close = cv2.GaussianBlur(img_close, (9, 9), 0)

    # filter out contours smaller than 9000 that is just noise
    cnts = cv2.findContours(img_close, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        if cv2.contourArea(c) < 10000:
            cv2.drawContours(img_close, [c], -1, (255, 255, 255), -1)

    cnts = cv2.findContours(img_close, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        if cv2.contourArea(c) > 1:
            cv2.drawContours(img_close, [c], -1, (255, 255, 255), -1)

    #Invert colors
    img_final = 255 - img_close


    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    img_final = cv2.dilate(img_final, kernel, iterations=2)

    # TODO TESTING
    #cv2.imshow('pro_resize', ResizeWithAspectRatio(img_final, height=1080))
    # TODO TESTING END

    # Find contours and filter using threshold area
    cnts = cv2.findContours(img_final, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    # Find rectangles, ignore the ones smaller than 50000 pixels and larger than 200000 px
    gray_without_contours = img_gray.copy()
    img_numb = 1
    images = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        # Assumes input image is 3024x4032 and earlier in the code up-scaled 1.5x to 4536x6048.
        # continue with rectangular contours between a range of 750x200px and 1300x500px.
        # the numbers bellow must be changed with camera resolution and distance from cassettes.
        if 750 < w < 1300 and 150 < h < 500:
            # Draws a rectangle on the contours that are recognized Only needed for testing
            # cv2.rectangle(img, (x, y), (x + w, y + h), (36, 255, 12), 2)

            # Cuts out contours in individual images
            images.append(
                {
                    "image_number":img_numb,
                    "image_data": img_gray[y:y+h, x:x+w],
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h
                }
            )
            img_numb += 1
            # Removes extracted contours from image
            cv2.rectangle(gray_without_contours, (x, y), (x + w, y + h), (255, 255, 255), -1)

    # Appends full image for unrecognized contours after loop
    images.append(
        {
            "image_number": 0,
            "image_data": gray_without_contours,
            "x": 0,
            "y": 0,
            "width": gray_without_contours.shape[1],
            "height": gray_without_contours.shape[0]
        }
    )

    # Process and threshold each image individually for better results
    for i in range(len(images)):
        images[i]["image_data"] = process_image_part(images[i]["image_data"], images[i]["image_number"])

    # Return a list of all images
    return images


def process_image_part(img, numb):
    # Binarize the image with an OTSU threshold function making the pixels either black or white

    # Todo Testing
    #cv2.imshow('pro_resize3', ResizeWithAspectRatio(img, height=1080, width=720))


    # Treat large image with OTSU thesholding and other images with an alterante OTSU
    if numb == 0:
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        #TODO FIX
       # dilated_img = cv2.dilate(img, np.ones((7, 7), np.uint8))
       # bg_img = cv2.medianBlur(dilated_img, 21)
       # diff_img = 255 - cv2.absdiff(img, bg_img)
       # norm_img = diff_img.copy()  # Needed for 3.x compatibility
       # cv2.normalize(diff_img, norm_img, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
       # _, thr_img = cv2.threshold(norm_img, 230, 0, cv2.THRESH_TRUNC)
       # cv2.normalize(thr_img, thr_img, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)



    # TODO TESTING
    #cv2.imshow('pro_resize2', ResizeWithAspectRatio(img, height=1080, width=720))
    #cv2.waitKey(0)
    #if numb == 0:
        #cv2.imshow('pro_resize2', ResizeWithAspectRatio(img, height=1080, width=720))
        #cv2.waitKey(0)
    # TODO TESTING END

    # Noise removal and contour filtering using a mask
    cnts = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    mask = img.copy()
    for c in cnts:
        if cv2.contourArea(c) < 10000:
            cv2.drawContours(mask, [c], -1, (0, 0, 0), -1)
    mask = 255 - mask
    img= cv2.bitwise_and(img, img, mask=mask)
    img = 255 - img

    #Todo move under noise removal
    # Apply blur to smoothen the image and remove noise
    img = cv2.GaussianBlur(img, (9, 9), 0)

    return img


@app.route('/api/image/<path:url>',)
def process(url):
    img = cv2.imread(url)
    # Rescale to 300DPI #TODO adjust for final camera setup
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    pro_images = pre_process(img)
    boxes = find_box(pro_images)
    return boxes


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)

