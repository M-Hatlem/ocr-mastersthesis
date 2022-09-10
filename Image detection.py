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
def find_pattern_matches(img, custom_config):
    text = pytesseract.image_to_string(img, config=custom_config)
    found = re.findall(r"HBE \d{5}\n\d{3} [O|B|C]\d{2}", text) # pattern here--- should be r"HBE \d{5}\n\d{3} [O|B|C]\d{2}$ #
    # Patteren is HBE (HELSE BERGEN) - ID (5 digit number) - (new line) - sample number (3 digits) - department and year - B/A/C - 2 digits)
    #print(found) # TODO TEST LINE
    return found


# Draw a box around each sentence and show the image TODO Make sentences
def box(img, pro_img):
    custom_config = r' -c tessedit_char_whitelist="HBECO0123456789 " --psm 3' # TODO FIX
    d = pytesseract.image_to_data(pro_img, output_type=pytesseract.Output.DICT, config=custom_config)
    pattern = r"HBE\d{5}\d{3}[O|B|C]\d{2}$"



    #TODO turn all of d[text] into string and then pre process the sting from there before applying regexp?? or will i loose find coordiantes??


    # Remove all empty strings the OCR interpreted lables / text cleaning
    d['text'] = [x.strip(' ') for x in d['text']]
    n_boxes = len(d['text'])
    words = []
    for i in range(n_boxes):
        if len(d['text'][i]) > 0:
            words.append(i)

    print((d['text'])) # TODO TEST LINE
    #print(words) # TODO TEST LINE
    # Iterate on the text and draw boxes where the pattern is found
    found = []
    for i in words:
        try:
            # Looks at each word and the five next words to see if it matches the pattern
            if re.match(pattern, d['text'][i] + d['text'][words[words.index(i)+1]] + d['text'][words[words.index(i)+2]] + d['text'][words[words.index(i)+3]]): # Alternative  re.match(pattern, d['text'][i] + d['text'][i + 1] + d['text'][i + 3] + d['text'][i + 4])
                found.append(d['text'][i] + d['text'][words[words.index(i)+1]] + d['text'][words[words.index(i)+2]] + d['text'][words[words.index(i)+3]])
                #print(d['text'][i] + d['text'][i + 1] + d['text'][i + 3] + d['text'][i + 4]) # TODO TEST LINE
                #print(d['text'][i] + d['text'][i + 1] + d['text'][i + 2] + d['text'][i + 3] + d['text'][i + 4]) # TODO TEST LINE
                # if there is a pattern match, get the coordinates draw a green box/rectangle the words.
                (x, y) = (d['left'][i], d['top'][i])
                (w1, h1, w2, h2) = (d['width'][i], d['height'][i], d['width'][words[words.index(i)+1]], d['height'][words[words.index(i)+3]])
                img = cv2.rectangle(img, (x, y), (x + w1 + w2, y + h1 + h2), (0, 255, 0), 12)
        except:
            pass

    print(found) # TODO TEST LINE
    print(len(found)) # TODO TEST LINE
    #print(len(find_pattern_matches(pro_img, custom_config))) # TODO TEST LINE

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
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Binarize the image with a threshold function making the pixels either black or white
    _, img_thres = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)


    # Apply dilation, erosion and blur to remove some noise and make the image easier to read


    # Noice removal and contour filtering
    cnts = cv2.findContours(img_thres, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    mask = img_thres.copy()
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        if cv2.contourArea(c) < 100000:
            cv2.drawContours(mask, [c], -1, (0, 0, 0), -1)

    #Countour Render test
    #cv2.drawContours(img, cnts, -1, (0, 255, 0), 3)
    #resize = ResizeWithAspectRatio(img, height=1080)
    #cv2.imshow('resize', resize)
    #cv2.waitKey(0)
    #quit()
    mask = 255 - mask
    img_pros = cv2.bitwise_and(img_thres, img_thres, mask=mask)
    img_pros = 255 - img_pros

    # TODO fine tune these parameters
    #kernel = np.ones((3, 3),  np.float32) / 9
    #img_pros = cv2.erode(img_pros, kernel, iterations=1)
    #img_pros = cv2.dilate(img_pros, kernel, iterations=1)
    # Apply blur to smooth out the edges
    img_pros = cv2.GaussianBlur(img_pros, (5, 5), 0)

    return img_pros


# Tests for running
if __name__ == "__main__":
    #img = cv2.imread("Images/IMG_0891.jpg")
    #img = cv2.imread("Images/IMG_0892.jpg")
    img = cv2.imread("Images/IMG_0894.jpg")
    #img = cv2.imread("pro_test.jpg")

    #TESTING
    #Rescale to 300DPI #TODO find alternative to rescaling for better results
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    #cv2.imwrite("test.jpg", img)    # TODO TEST

    pro_img = pre_process(img)
    #cv2.imwrite("pro_test.jpg", pro_img)   # TODO TEST

    #Testing for PSM
    #custom_config = r' -c tessedit_char_whitelist="HBEOC0123456789 "'
    #print(pytesseract.image_to_string(pro_img, config=custom_config)) # Prints the image text
    #print(len(find_pattern_matches(pro_img, custom_config)))
    #quit()


    box(img, pro_img)


    # TODO
    #pattern = r"HBE \d{5}\n\d{3} [O|B|C]\d{2}$"
    # find casettes without a pattern
    # Develop a UI
