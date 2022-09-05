import cv2
import pytesseract
import numpy as np
import re as re


# rezise image for showing in dev, only needed when viewing in python. Can remove when custom UI is added.
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


# finds and returns the casettes with a recongizable pattern from an image
def find_pattern_matches(img):
    text = pytesseract.image_to_string(img)
    found = re.findall(r"HBE \d{5}\n\d{3} [O|B|C]\d{2}", text) # pattern here--- should be r"HBE \d{5}\n\d{3} [O|B|C]\d{2}$ #
    # Patteren is HBE (HELSE BERGEN) - ID (5 digit number) - (new line) - sample number (3 digits) - department and year - B/A/C - 2 digits)
    return found


# Draw a box around each sentence and show the image TODO Make sentences
def box(img, pro_img):
    d = pytesseract.image_to_data(pro_img, output_type=pytesseract.Output.DICT)
    pattern = r"HBE\d{5}\d{3}[O|B|C]\d{2}$"

    n_boxes = len(d['text'])
    for i in range(n_boxes):
        try:
            # Looks at each word and the five next words to see if it matches the pattern
            if re.match(pattern, d['text'][i] + d['text'][i + 1] + d['text'][i + 2] + d['text'][i + 3] + d['text'][i + 4]):
                # print(d['text'][i] + d['text'][i + 1] + d['text'][i + 2] + d['text'][i + 3] + d['text'][i + 4])
                # if there is a pattern match, get the coordinates draw a green box/rectangle the words.
                (x, y) = (d['left'][i], d['top'][i])
                (w1, h1, w2, h2) = (d['width'][i], d['height'][i], d['width'][i+1], d['height'][i+3])
                img = cv2.rectangle(img, (x, y), (x + w1 + w2, y + h1 + h2), (0, 255, 0), 12)
        except:
            pass

    #Display the images in python, can be removed once UI is added
    resize = ResizeWithAspectRatio(img, height=1080)
    cv2.imshow('resize', resize)
    pro_resize = ResizeWithAspectRatio(pro_img, height=1080)
    cv2.imshow('pro_resize', pro_resize)
    cv2.waitKey(0)


# This function pre-processes the images
def pre_process(img):
    # TODO edit color on grey cassetes? use a map or filter?

    # Convert image to greyscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Binarize the image with a threshold function making the pixels either black or white
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    img = cv2.bitwise_not(img)


    # Apply dilation, erosion and blur to remove some noise and make the image easier to read
    # TODO fine tune these parameters
    kernel = np.ones((3, 3),  np.float32) / 9
    img = cv2.erode(img, kernel, iterations=1)
    img = cv2.dilate(img, kernel, iterations=1)
    # Apply blur to smooth out the edges
    img = cv2.GaussianBlur(img, (5, 5), 0)

    return img


# Tests for running
if __name__ == "__main__":
    #img = cv2.imread("Images/IMG_0891.jpg")
    img = cv2.imread("Images/IMG_0894.jpg")

    #TESTING
    #Rescale to 300DPI #TODO find alternative to rescaling for better results
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    #cv2.imwrite("test.jpg", img)

    pro_img = pre_process(img)

    #print(pytesseract.image_to_string(pro_img)) # Prints the image text
    box(img, pro_img)


    # TODO
    #pattern = r"HBE \d{5}\n\d{3} [O|B|C]\d{2}$"
    # find casettes without a pattern
    # Develop a UI
