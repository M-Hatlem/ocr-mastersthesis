import cv2
import pytesseract
import numpy as np
import re as re
import pandas as pd


# rezise image for showing, only needed when viewing in python. Can remove when propper UI is added.
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


def find_pattern_matches(img):
    text = pytesseract.image_to_string(img)
    found = re.findall(r"HBE \d{5}\n\d{3} [O|B|C]\d{2}", text) # pattern here--- should be r"HBE \d{5}\n\d{3} [O|B|C]\d{2}$
    return found


# Draw a box around each word TODO Make sentences
def box(img, pro_img):
    d = pytesseract.image_to_data(pro_img, output_type=pytesseract.Output.DICT)
    pattern = r"HBE \d{5}\n\d{3} [O|B|C]\d{2}"
    n_boxes = len(d['text'])
    for i in range(n_boxes):
        if int(float(d['conf'][i])) > 60:
            if re.match(pattern, d['text'][i]):
                print(d['text'][i])
                (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 12)
            else:
                (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 12)
    resize = ResizeWithAspectRatio(img, height=1080)
    cv2.imshow('resize', resize)
    pro_resize = ResizeWithAspectRatio(pro_img, height=1080)
    cv2.imshow('pro_resize', pro_resize)
    cv2.waitKey(0)


def gray_dialate(img):

    # TODO remove color?
    #black = np.array([0, 0, 0])
    #img = cv2.inRange(img, black, black)

    # TODO Convert to gray
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Canny binarize alternative
    #img = cv2.Canny(image, 150, 200, True)
    # TODO Binarize better!
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    img = cv2.bitwise_not(img)


    # Apply dilation and erosion to remove some noise
    kernel = np.ones((1, 1), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)
    # Apply blur to smooth out the edges
    img = cv2.GaussianBlur(img, (5, 5), 0)

    return img


if __name__ == "__main__":
    #img = cv2.imread("Images/IMG_0891.jpg")
    img = cv2.imread("Images/IMG_0894.jpg")

    #TESTING
    #Rescale to 300DPI
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)


    pro_img = gray_dialate(img)


    #print(pytesseract.image_to_string(pro_img)) # Prints the image text
    box(img, pro_img)


    # TODO
    # Get image read
    # Find patterns of text from casettes # Patteren is HBE (HELSE BERGEN) - ID (5 digit number) - (new line) - sample number (3 digits) - department and year - B/A/C - 2 digits)
    #pattern = r"HBE \d{5}\n\d{3} [O|B|C]\d{2}$"
    # report missing patterns
    # show correct patterns
