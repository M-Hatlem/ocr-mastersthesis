# ocr-master

Digitizing pathology lab workflows using image processing and OCR

Install instructions for DEV kit
1. First clone from GitHUb with the commnad:


    ```git clone https://github.com/M-Hatlem/ocr-master```
2. Download [node](https://nodejs.org/en/download/) (recommended is latest LTS) (16.18.0 used for development)
3. Install electron (Developed using version 21.0.1) by navigating to the Ocr-Master directory and running the command
    
    ```npm install electron --save```
4. Download [Python](https://www.python.org/downloads/) (Developed using Python 3.10) and setup a Venv with flask, tessaract and CV2 by running:
   
   ```pip install flask tessaract cv2 numpy```
5. Move the Python Venv into Ocr-Master/Python/ --> should look like Ocr-Master/Python/Venv....
6. Install [Tessaract](https://tesseract-ocr.github.io/tessdoc/Downloads.html) and add it to the [console/Path](https://ironsoftware.com/csharp/ocr/blog/ocr-tools/tesseract-ocr-windows/)
7. Run the app using "npm start" from Ocr-Master in command line
    
    ```npm start```
