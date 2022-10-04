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
    let canvas = document.getElementById('canvas');
    context = canvas.getContext('2d');
    let img = document.createElement("img");
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
            let x = event.pageX - canvas.offsetLeft,
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

// Searches to see if x and y is within a box, then open a casette window
function search_box(list, x, y, resize) {
    for (i=0; i< list.length; i++) {
        let text = list[i][0]
        let left = list[i][1]/resize
        let top = list[i][2]/resize
        let width = list[i][3]/resize
        let height = list[i][4]/resize
        if (y > top && y < top  + height  && x > left  && x < left  + width ) {
            let popup = document.getElementById("Popup");
            let popup_text = document. getElementsByClassName("popuptext");
            let canvas = document.getElementById('canvas');
            if (popup.classList[1] != "show") {
                popup.style.left = (left + (width/2) + canvas.offsetLeft) +"px";
                popup.style.top = (top + canvas.offsetTop) + "px";
                original = text
                text = text.replace("NONE", "")
                values = text.split("-")
                popup_text[0].value = values[0]
                popup_text[1].value = values[1]
                popup_text[2].value = values[2]
                popup.classList.add("show");
                return current_elm = list[i]
            }
        }
    }
}

//closese the casette window if all inputs match correct pattern, otherwise highlight the missing value
function close_popup() {
    let popup_text = document. getElementsByClassName("popuptext");
    correct = 0
    switch (/^\d{5}$/.test(popup_text[0].value)) {
        case true:
            popup_text[0].style.borderColor = "dimgrey";
            correct +=1
            break;
        case false:
            popup_text[0].style.borderColor = "red"
            break;
        }
    switch (/^\d{3}$/.test(popup_text[1].value)) {
        case true:
            popup_text[1].style.borderColor = "dimgrey";
            correct +=1
            break;
        case false:
            popup_text[1].style.borderColor = "red"
            break;
        }
    switch (/^[O|o|B|b|C|c|]\d{2}$/.test(popup_text[2].value)) {
        case true:
            popup_text[2].style.borderColor = "dimgrey";
            correct +=1
            break;
        case false:
            popup_text[2].style.borderColor = "red"
            break;
        }
    if (correct == 3) {
        item_update = popup_text[0].value + "-" + popup_text[1].value + "-" + popup_text[2].value
        update_lists(item_update)
    } 


//Update complete and partial lists with selected elements
function update_lists(item_update) {
    if (complete.includes(current_elm)) {
        let i = complete.indexOf(current_elm)
        complete[i][0] = item_update
        }
    else if (partial.includes(current_elm)) {
        let i = partial.indexOf(current_elm)
        partial.splice(i, 1)
        current_elm[0] = item_update
        complete.push(current_elm)
        draw_boxes([current_elm], "LawnGreen", context)
        }
    let popup = document.getElementById("Popup");
    popup.classList.remove("show")
    }
}


//loading screen
function start_loading() {
    document.getElementsByClassName('page-1')[0].style.display = 'none';
    document.getElementsByClassName('loading')[0].style.display = 'table';
}



