import cv2
import pytesseract
import re as re
import json
import math
import numpy as np
import sys
import time
from flask import Flask

app = Flask(__name__)

# rezise image for showing in tests and debugging
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
def find_box(pro_images, nn):
    # loops through all images and applies OCR
    complete = []
    partial = []
    custom_config = r' -c tessedit_char_whitelist="HBECO0123456789 " --psm 3'  # Config for tesseract
    for j in range(len(pro_images)):
        found = False
        img = pro_images[j]["image_data"]
        t_output = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config)

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
                    found = True
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
                        found = True
                        complete.append({
                            "id": t_output['text'][words[words.index(i) + 1]] + "-" + t_output['text'][words[words.index(i) + 2]] + "-" + t_output['text'][words[words.index(i) + 3]],
                            "left": t_output['left'][i+1] + pro_images[j]["x"],
                            "top": t_output['top'][i+1] + pro_images[j]["y"],
                            "width": t_output['width'][i+1],
                            "height": t_output['height'][i+1] * 2})
                    elif pattern_2 is None:
                        found = True
                        partial.append({
                            "id": "NONE" + "-" + t_output['text'][words[words.index(i) + 2]] + "-" + t_output['text'][words[words.index(i) + 3]],
                            "left": t_output['left'][i] + pro_images[j]["x"],
                            "top": t_output['top'][i] + pro_images[j]["y"],
                            "width": t_output['left'][i+2] + t_output['width'][i+2] - t_output['left'][i],
                            "height": t_output['top'][i+2] + t_output['height'][i+2] - t_output['top'][i]})
                    elif pattern_3 is None:
                        found = True
                        partial.append({
                            "id": t_output['text'][words[words.index(i) + 1]] + "-" + "NONE" + "-" + t_output['text'][words[words.index(i) + 3]],
                            "left": t_output['left'][i] + pro_images[j]["x"],
                            "top": t_output['top'][i] + pro_images[j]["y"],
                            "width": t_output['left'][i+1] + t_output['width'][i+1] - t_output['left'][i],
                            "height": t_output['top'][i+3] + t_output['height'][i+3] - t_output['top'][i]})
                    elif pattern_4 is None:
                        found = True
                        partial.append({
                            "id": t_output['text'][words[words.index(i) + 1]] + "-" + t_output['text'][words[words.index(i) + 2]] + "-" + "NONE",
                            "left": t_output['left'][i] + pro_images[j]["x"],
                            "top": t_output['top'][i] + pro_images[j]["y"],
                            "width": t_output['left'][i+1] + t_output['width'][i+1] - t_output['left'][i],
                            "height": t_output['top'][i+2] + t_output['height'][i+2] - t_output['top'][i]})
            except IndexError:
                pass

        if nn and not found:
            partial.append({
                "id": "NONE-NONE-NONE",
                "left":pro_images[j]["x"],
                "top": pro_images[j]["y"],
                "width":pro_images[j]["width"],
                "height": pro_images[j]["height"]})

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
        images[i]["image_data"] = process_image_part(images[i]["image_data"])

    # Return a list of all images
    return images


def process_image_part(img):
    # Binarize the image with an OTSU threshold function making the pixels either black or white
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

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

    # Apply blur to smoothen the image and remove noise
    img = cv2.GaussianBlur(img, (9, 9), 0)
    return img


# use east text detecion neural network to find rectangles
# model found here: https://www.dropbox.com/s/r2ingd0l3zt8hxs/frozen_east_text_detection.tar.gz?dl=1
def east_detection(img):
    # Scale image to work with east, need to be a multiple of 32
    original_width = img.shape[1]
    origianl_height = img.shape[0]
    inp_width = (math.ceil(img.shape[1]/32) * 32) - img.shape[1]
    inp_height = (math.ceil(img.shape[0]/32) * 32) - img.shape[0]
    img = cv2.copyMakeBorder(src=img, top=0, bottom=inp_height, left=0, right=inp_width, borderType=cv2.BORDER_CONSTANT)

    # Run east-text detection NN
    net = cv2.dnn.readNet("./Python/frozen_east_text_detection.pb")
    blob = cv2.dnn.blobFromImage(img, 1.0, (img.shape[1], img.shape[0]), (123.68, 116.78, 103.94), True, False)
    outputLayers = []
    outputLayers.append("feature_fusion/Conv_7/Sigmoid")
    outputLayers.append("feature_fusion/concat_3")
    net.setInput(blob)
    output = net.forward(outputLayers)
    scores = output[0]
    geometry = output[1]
    [rects, confidences] = decodeBoundingBoxes(scores, geometry, 0.5)
    indices = cv2.dnn.NMSBoxesRotated(rects, confidences, 0.5, 0.4)

    # get boxes from EAST result
    boxes = []
    total_height = []
    total_width = []
    for i in indices:
        # get 4 corners of the rotated rect
        vertices = cv2.boxPoints(rects[i])
        # scale the bounding box coordinates based on the respective ratios
        x = int(vertices[0][0])
        y = int(vertices[1][1])
        w = int(vertices[2][0]) - int(vertices[0][0])
        h = int(vertices[0][1]) - int(vertices[1][1])
        boxes.append([[x,y], [x+w, y+h]])
        total_height.append(h)
        total_width.append(w)

    # Merge boxes modifed from https://stackoverflow.com/questions/66490374/how-to-merge-nearby-bounding-boxes-opencv
    merge_height = int((sum(total_height) / len(total_height)) / 3)
    merge_width = int((sum(total_width) / len(total_width)) * 1.5)
    max_height = int(merge_height * 8)
    max_width = int(merge_width * 4)
    boxes = sorted(boxes, key=lambda k: [k[0][0], k[0][1]], reverse=True)
    merge_boxes(boxes, img, merge_height, merge_width, max_height, max_width, False) # Merges the boxes, set final flag to True to animate

    # Filter out boxes smaller than half the median value
    box_width = []
    for box in boxes:
        box_width.append(box[1][0] - box[0][0])
    box_width.sort()
    width_threshold = int((box_width[int((len(box_width))/2)]/1.5))

    #Get box coords
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_numb = 1
    images = []
    padding = 10
    for box in boxes:
        # add padding to get some extra pixels around the number
        x = box[0][0] - padding
        if x <= 0:
            x = x + padding
        y = box[0][1] - padding
        if y <= 0:
            y = y + padding
        w = (box[1][0] - box[0][0]) + (padding*2)
        if x + w > original_width:
            w = w - padding
        h = (box[1][1] - box[0][1]) + (padding*2)
        if y + h > origianl_height:
            h = h - padding
        # if box is not too small add it to a list of images to be processed
        if w > width_threshold:
            images.append(
                {
                    "image_number": img_numb,
                    "image_data": img_gray[y:y + h, x:x + w],
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h
                })

    # pre process images
    for i in range(len(images)):
        images[i]["image_data"] = process_image_part(images[i]["image_data"])

    return images


def merge_boxes(boxes, img, merge_height, merge_width, max_height, max_width, animate):
    highlight = [[0, 0], [1, 1]]
    points = [[[0, 0]]]
    finished = False
    while not finished:
        # set end con
        finished = True

        if animate:
            copy = np.copy(img);
            for box in boxes:
                cv2.rectangle(copy, tup(box[0]), tup(box[1]), (0, 200, 0), 10);
            cv2.rectangle(copy, tup(highlight[0]), tup(highlight[1]), (0, 0, 255), 10);
            for point in points:
                point = point[0];
                cv2.circle(copy, tup(point), 4, (255, 0, 0), 10);
            cv2.imshow("Copy", ResizeWithAspectRatio(copy, height=1080));
            key = cv2.waitKey(1);
            time.sleep(0.3)
            if key == ord('q'):
                break;

        # loop through boxes
        index = len(boxes) - 1
        while index >= 0:
            # grab current box
            curr = boxes[index]

            # add margin
            tl = curr[0][:]
            br = curr[1][:]
            # tl[0] -= merge_width
            # tl[1] -= merge_height
            br[0] += merge_width
            br[1] += merge_height

            # find overlaps
            overlaps = getAllOverlaps(boxes, [tl, br], index)

            # check if empty
            if len(overlaps) > 0:
                # combine boxes
                # convert to a contour
                con = []
                overlaps.append(index)
                for ind in overlaps:
                    tl, br = boxes[ind]
                    con.append([tl])
                    con.append([br])
                con = np.array(con)

                # get bounding rect
                x, y, w, h = cv2.boundingRect(con)

                if w < max_width and h < max_height:
                    # stop growing
                    w -= 1
                    h -= 1
                    merged = [[x, y], [x + w, y + h]]
                    highlight = merged[:];
                    points = con;

                    # remove boxes from list
                    overlaps.sort(reverse=True)
                    for ind in overlaps:
                        del boxes[ind]
                    boxes.append(merged)

                    # set flag
                    finished = False
                    break

            # increment
            index -= 1

    # Fixes missing overlaps without taking the expanded radius into consideration
    if merge_height != 0 and merge_width != 0:
        merge_boxes(boxes, img, 0, 0, int(max_height*1.2), int(max_width*1.2), animate)
    return boxes


# returns true if the two boxes overlap
def overlap(source, target):
    # unpack points
    tl1, br1 = source
    tl2, br2 = target

    # checks
    if (tl1[0] >= br2[0] or tl2[0] >= br1[0]):
        return False
    if (tl1[1] >= br2[1] or tl2[1] >= br1[1]):
        return False
    return True


# returns all overlapping boxes
def getAllOverlaps(boxes, bounds, index):
    overlaps = []
    for a in range(len(boxes)):
        if a != index:
            if overlap(bounds, boxes[a]):
                overlaps.append(a)
    return overlaps


# Tuplify
def tup(point):
    return (point[0], point[1]);


# bounding box decoding
# Modified from https://github.com/opencv/opencv/blob/master/samples/dnn/text_detection.py
def decodeBoundingBoxes(scores, geometry, scoreThresh):
    detections = []
    confidences = []
    height = scores.shape[2]
    width = scores.shape[3]
    for y in range(0, height):

        # Extract data from scores
        scoresData = scores[0][0][y]
        x0_data = geometry[0][0][y]
        x1_data = geometry[0][1][y]
        x2_data = geometry[0][2][y]
        x3_data = geometry[0][3][y]
        anglesData = geometry[0][4][y]
        for x in range(0, width):
            score = scoresData[x]

            # If score is lower than threshold score, move to next x
            if (score < scoreThresh):
                continue

            # Calculate offset
            offsetX = x * 4.0
            offsetY = y * 4.0
            angle = anglesData[x]

            # Calculate cos and sin of angle
            cosA = math.cos(angle)
            sinA = math.sin(angle)
            h = x0_data[x] + x2_data[x]
            w = x1_data[x] + x3_data[x]

            # Calculate offset
            offset = ([offsetX + cosA * x1_data[x] + sinA * x2_data[x], offsetY - sinA * x1_data[x] + cosA * x2_data[x]])

            # Find points for rectangle
            p1 = (-sinA * h + offset[0], -cosA * h + offset[1])
            p3 = (-cosA * w + offset[0], sinA * w + offset[1])
            center = (0.5 * (p1[0] + p3[0]), 0.5 * (p1[1] + p3[1]))
            detections.append((center, (w, h), -1 * angle * 180.0 / math.pi))
            confidences.append(float(score))

    # Return detections and confidences
    return [detections, confidences]


@app.route('/api/image/<path:url>/<nn>',)
def process(url, nn):
    print("Starting image processing", file=sys.stderr)
    img = cv2.imread(url)
    # Rescale to 300DPI #TODO adjust for final camera setup
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    if nn == "True":
        print("Processing with NN", file=sys.stderr)
        nn = True
        pro_images = east_detection(img)
    else:
        nn = False
        print("Processing without NN", file=sys.stderr)
        pro_images = pre_process(img)
    print("Starting OCR", file=sys.stderr)
    boxes = find_box(pro_images, nn)
    return boxes


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)

