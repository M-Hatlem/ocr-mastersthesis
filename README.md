# ocr-master

Digitizing pathology lab workflows using image processing and OCR

Install instructions for DEV kit
1. First clone from GitHUb with the commnad:
    ```git clone https://github.com/M-Hatlem/ocr-master```
2. Download node from: https://nodejs.org/en/download/ (recommended is latest LTS) (16.18.0 used for development)
3. Install electron (Developed using version 21.0.1) by navigating to the Ocr-Master directory and running the command 
    ```npm install electron --save```
4. Download Python and setup a Venv with flask, tessaract and CV2 by running: (Developed using Python 3.10)
    ```pip install flask tessaract cv2 numpy```
5. Move the Python Venv into Ocr-Master/Python/ --> should look like Ocr-Master/Python/Venv....
6. Install Tessaract and add it to the console/Path
7. Run the app using "npm start" from Ocr-Master in command line
    ```npm start```
