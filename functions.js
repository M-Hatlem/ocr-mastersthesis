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
    var canvas = document.getElementById('canvas');
    var context = canvas.getContext('2d');
    var img = document.createElement("img");
    img.src = String(image["path"])
    img.onload = function(){
        canvas.width = img.width*1.5
        canvas.height = img.height*1.5
        context.drawImage(img, 0, 0, img.width*1.5, img.height*1.5);
        // Iterate over the data from the backend, the correctly identified ones
        complete = data_list[0] // fully identified entries
        draw_boxes(complete, "LawnGreen", context)
        // Iterate over the data from the backend, the partially identified ones
        partial = data_list[1] // partially identified entries
        draw_boxes(partial, "orange", context)
        //add the ability to click on the rectang
        canvas.addEventListener('click', function (event) {
            var x = event.pageX - canvas.offsetLeft,
            y = event.pageY - canvas.offsetTop;
            search_box(complete, x, y, resizer)
            search_box(partial, x, y, resizer)
        }, false);

        //Rezise canvas to fit screen
        resizer = 8 // Divide by 8 to resize
        canvas.style.height = canvas.height/resizer + "px"

        //Remove loading screen, display image
        document.getElementsByClassName('loading')[0].style.display = 'none';
        document.getElementById('canvas').style.display = 'inline'; 
    }
}

//Used to draw boxes from the partial and complete lists from backend
function draw_boxes(list, color, context) {
    for (i=0; i< list.length; i++) {
        context.beginPath();
        context.rect(list[i][1], list[i][2], list[i][3], list[i][4]);
        context.shadowColor = "black"
        context.shadowBlur = 20;
        context.lineJoin = "bevel";
        context.strokeStyle = color;
        context.lineWidth = 15;
        context.stroke();
    }
}

// Searches to see if x and y is within a box
function search_box(list, x, y, resize) {
    for (i=0; i< list.length; i++) {
        if (y > list[i][2]/resize && y < list[i][2]/resize  + list[i][4]/resize  && x > list[i][1]/resize  && x < list[i][1]/resize  + list[i][3]/resize ) {
            casette_window(list[i][0])
        }
    }
}


// open window with casette information
function casette_window(text) {
    console.log(text);

}



//loading screen
function start_loading() {
    document.getElementsByClassName('page-1')[0].style.display = 'none';
    document.getElementsByClassName('loading')[0].style.display = 'table';
}


