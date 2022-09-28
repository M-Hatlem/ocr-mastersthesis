//this file contains the fucnctions called when running the application

//passes the image to the backend
function process_image(image) {
    image_path = String(image["path"])
    fetch(`http://127.0.0.1:5000/api/image/`+ image_path)  // TODO FIX HERE!!!
      .then((response) => response.json())
      .then((data) => format_image(image, data));
}

//code for uploading an image
function upload_image() {
    const uploadFile = document.getElementById("image-input").files[0]
    start_loading()
    process_image(uploadFile)
}

//Taking a photo
function take_image() { 
}

// Formating the image with the data from the backend to highlight the detected casettes
function format_image(image, data_list) {
    complete = data_list[0] // fully identified entries
    partial = data_list[1] // partially identified entries
    var canvas = document.getElementById('canvas');
    var context = canvas.getContext('2d');
    var img = document.createElement("img");
    img.src = String(image["path"])
    img.onload = function(){
        canvas.width = img.width*1.5
        canvas.height = img.height*1.5
        context.drawImage(img, 0, 0, img.width*1.5, img.height*1.5);
        
        for (i=0; i< complete.length; i++) {
            context.beginPath();
            context.rect(complete[i][1], complete[i][2], complete[i][3] * 2.5, complete[i][4] * 2.5);
            context.shadowColor = "black"
            context.shadowBlur = 20;
            context.lineJoin = "bevel";
            context.strokeStyle = 'LawnGreen';
            context.lineWidth = 15;
            context.stroke();
        }
        for (i=0; i< partial.length; i++) {
            context.beginPath();
            context.rect(partial[i][1], partial[i][2], partial[i][3] * 2.5, partial[i][4] * 2.5);
            context.shadowColor = "black"
            context.shadowBlur = 20;
            context.lineJoin = "bevel";
            context.strokeStyle = 'orange';
            context.lineWidth = 15;
            context.stroke();
        }
        document.getElementsByClassName('loading')[0].style.display = 'none';
        document.getElementById('canvas').style.display = 'inline';
    }
}

//loading screen
function start_loading() {
    document.getElementsByClassName('page-1')[0].style.display = 'none';
    document.getElementsByClassName('loading')[0].style.display = 'table';
}
