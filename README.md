# ocr-mastersthesis

Digitizing pathology lab workflows using image processing and OCR -  mastersthesis

Install instructions for DEV kit
1. First install Git and clone the repository from GitHub with the commnad:


    ```git clone https://github.com/M-Hatlem/ocr-masterthesis```
2. Download [node](https://nodejs.org/en/download/) (recommended is latest LTS) (16.18.0 used for development)
3. Install electron (Developed using version 21.0.1) by navigating to the Ocr-Master directory and running the command:
    
    ```npm install electron --save```
4. Download [Python](https://www.python.org/downloads/) (Developed using Python 3.10) and setup a Venv with flask, tessaract and CV2 by running:
   
   ```pip install flask tessaract cv2 numpy```
5. Move the Python Venv into Ocr-Masterthesis/Python/ --> should look like Ocr-Masterthesis/Python/Venv....
6. Download [EAST text detector](https://www.dropbox.com/s/r2ingd0l3zt8hxs/frozen_east_text_detection.tar.gz?dl=1) and place the file in Ocr-Masterthesis/Python/
7. Install [Tessaract](https://tesseract-ocr.github.io/tessdoc/Downloads.html) and add it to the [console/Path](https://ironsoftware.com/csharp/ocr/blog/ocr-tools/tesseract-ocr-windows/)
8. Run the app using "npm start" from Ocr-Masterthesis in command line
    
    ```npm start```
