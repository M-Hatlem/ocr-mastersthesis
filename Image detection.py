import cv2
import pytesseract
import numpy as np
import re as re

#rezise image for showing
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

#Draw a box around each letter
def box_letters(img, pro_img):
    h, w, c = img.shape
    boxes = pytesseract.image_to_boxes(img)
    for b in boxes.splitlines():
        b = b.split(' ')
        img = cv2.rectangle(img, (int(b[1]), h - int(b[2])), (int(b[3]), h - int(b[4])), (0, 0, 255), 2)

    resize = ResizeWithAspectRatio(img, height=1080)
    cv2.imshow('resize', resize)
    cv2.waitKey(0)


#Draw a box around each word
def box_words(img, pro_img):
    d = pytesseract.image_to_data(pro_img, output_type=pytesseract.Output.DICT)
    #print(d.keys())

    n_boxes = len(d['text'])
    for i in range(n_boxes):
        if int(float(d['conf'][i])) > 60:
            (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            pro_img = cv2.rectangle(pro_img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    resize = ResizeWithAspectRatio(img, height=1080)
    cv2.imshow('resize', resize)
    pro_resize = ResizeWithAspectRatio(pro_img, height=1080)
    cv2.imshow('pro_resize', pro_resize)
    cv2.waitKey(0)


#Draw a box around a pattern
def box_pattern(img, pro_img):
    d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    keys = list(d.keys())

    pattern = '^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/(19|20)\d\d$'
    #Pattern for date..

    n_boxes = len(d['text'])
    for i in range(n_boxes):
        if int(d['conf'][i]) > 60:
            if re.match(pattern, d['text'][i]):
                (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    resize = ResizeWithAspectRatio(img, height=1080)
    cv2.imshow('resize', resize)
    cv2.waitKey(0)

#pre-proecssing methods
# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


#canny edge detection
def canny(image):
    return cv2.Canny(image, 150, 200, True)


def gray_dialate(img):

    # TODO remove color
    #black = np.array([0, 0, 0])
    #img = cv2.inRange(img, black, black)

    # TODO Convert to gray
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


    #img = canny(img)
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


    print(pytesseract.image_to_string(pro_img))
    box_words(img, pro_img)
    #box_letters(img, pro_img)
    #box_pattern(img, pro_img)



    # TODO
    # Get image read
    # Find patterns of text from casettes
    # report missing patterns
    # show correct patterns
