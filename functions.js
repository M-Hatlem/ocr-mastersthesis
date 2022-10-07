// This file contains the fucnctions called when running the application

// passes the image to the backend
function process_image(image) {
    image_path = String(image["path"])
    fetch(`http://127.0.0.1:5000/api/image/`+ image_path)
      .then((response) => response.json())
      .then((data) => format_image(image, data));
}

// code for uploading an image
function upload_image() {
    const uploadFile = document.getElementById("image-input").files[0]
    start_loading()
    process_image(uploadFile)
}

// Takes a photo
function take_image() {
    //Save image or overwrite old image 
    //get image_path
    start_loading()
    process_image(//*image_path*// 
    )
}

// Formating the image with the data from the backend to highlight the detected casettes and sets up the canvas
function format_image(image, data_list) {
    let canvas = document.getElementById('canvas');
    context = canvas.getContext('2d');
    let img = document.createElement("img");
    img.src = String(image["path"])
    img.onload = function(){
        canvas.width = img.width*1.5
        canvas.height = img.height*1.5
        context.drawImage(img, 0, 0, img.width*1.5, img.height*1.5);
        // Rezise canvas to fit screen
        resizer = 8 // Divide by 8 to resize //TODO update with new camera
        canvas.style.height = canvas.height/resizer + "px"
        // Iterate over the data from the backend, the correctly identified ones
        complete = data_list[0] // fully identified entries
        draw_boxes(complete, "LawnGreen", context)
        // Iterate over the data from the backend, the partially identified ones
        partial = data_list[1] // partially identified entries
        draw_boxes(partial, "orange", context)
        // sets up for cusom drawn boxes
        current_elm = ""
        cusomt_box = ""

        //add the ability to click on the rectang
        canvas.addEventListener('click', function (event) {
            let x = event.pageX - canvas.offsetLeft;
            let y = event.pageY - canvas.offsetTop;
            search_box(complete, x, y, resizer)
            search_box(partial, x, y, resizer)
        });
        
        // listen for mouse held down
        var MouseIsDown = false;
        canvas.addEventListener('mousedown', function (event) {
            // if you are not clicking a popup box
            let x = event.pageX - canvas.offsetLeft;
            let y = event.pageY - canvas.offsetTop;
            if (search_box(complete, x, y, resizer) == false && search_box(partial, x, y, resizer) == false) {
                //if a popup box is not open continue
                let popup = document.getElementById("Popup");
                if (popup.classList[1] != "show") {
                    custom_startX = x * resizer;
                    custom_startY = y * resizer;
                    MouseIsDown = true;
                    // Create overlay to draw on to avoid reseting the canvas
                    overlay = document.createElement("canvas");
                    overlay.id = "overlay"
                    overlay.width = canvas.width
                    overlay.height = canvas.height
                    overlay.style.height = canvas.height/resizer + "px"
                    var doc = document.getElementsByClassName("image")[0];
                    canvas.style.position = "absolute"
                    doc.appendChild(overlay)
                    ovleray_ctx = overlay.getContext("2d")
                    ovleray_ctx.strokeStyle = "LawnGreen";
                    ovleray_ctx.lineWidth = 15;

                    // Tracks mouse movement on the overlay if mouse is held down
                    overlay.addEventListener('mousemove', function (event) {
                        if (MouseIsDown) {
                            let x = event.pageX - canvas.offsetLeft;
                            let y = event.pageY - canvas.offsetTop;
                            custom_width = (x * resizer) - custom_startX;
                            custom_height = (y * resizer) - custom_startY;     
                            ovleray_ctx.clearRect(0, 0, overlay.width, overlay.height);
                            ovleray_ctx.strokeRect(custom_startX, custom_startY, custom_width, custom_height);
                        }
                    });

                    // listen for user letting go of the mouse and draws a square
                    overlay.addEventListener('mouseup', function () {
                        if (MouseIsDown) {
                            MouseIsDown = false;
                            canvas.style.position = "relative"
                            document.getElementById("overlay").remove()
                            custom_box = {
                                "left": custom_startX,
                                "top": custom_startY,
                                "width": custom_width,
                                "height": custom_height
                            }
                            draw_boxes([custom_box], "LawnGreen", context)
                            let popup = document.getElementById("Popup");
                            let popup_text = document. getElementsByClassName("popuptext");
                            popup.style.left = ((custom_startX/resizer) + ((custom_width/resizer)/2) + canvas.offsetLeft) +"px";
                            popup.style.top = ((custom_startY/resizer) + canvas.offsetTop) + "px";
                            popup_text[0].value = ""
                            popup_text[1].value = ""
                            popup_text[2].value = ""
                            popup.classList.add("show");
                        }
                    });

                } 
            }
        });


        // Remove loading screen and display image once listeners and canvas has finished loading
        document.getElementsByClassName('loading')[0].style.display = 'none';
        document.getElementById('canvas').style.display = 'inline';
    }
}

// Used to draw boxes from the partial and complete lists from backend
function draw_boxes(list, color, context) {
    for (i=0; i< list.length; i++) {
        context.beginPath();
        context.rect(list[i]["left"], list[i]["top"], list[i]["width"], list[i]["height"]);
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
    let popup = document.getElementById("Popup");
    if (popup.classList[1] != "show") {
        for (i=0; i < list.length; i++) {
            let text = list[i]["id"]
            let left = list[i]["left"]/resize
            let top = list[i]["top"]/resize
            let width = list[i]["width"]/resize
            let height = list[i]["height"]/resize
            if (y > top && y < top  + height  && x > left  && x < left  + width ) {
                let canvas = document.getElementById('canvas');
                let popup_text = document. getElementsByClassName("popuptext");
                popup.style.left = (left + (width/2) + canvas.offsetLeft) +"px";
                popup.style.top = (top + canvas.offsetTop) + "px";
                original = text
                text = text.replace("NONE", "")
                values = text.split("-")
                popup_text[0].value = values[0]
                popup_text[1].value = values[1]
                popup_text[2].value = values[2]
                popup.classList.add("show");
                current_elm = list[i]
                return true
            }
        }
    }
    return false
}

// closese the casette window if all inputs match the correct pattern, otherwise highlight the missing values
function close_popup() {
    let popup_text = document. getElementsByClassName("popuptext");
    correct = 0
    expressions = [/^\d{5}$/, /^\d{3}$/, /^[O|o|B|b|C|c|]\d{2}$/]
    for (i=0; i < expressions.length; i++) {
        switch (expressions[i].test(popup_text[i].value)) {
            case true:
                popup_text[i].style.borderColor = "dimgrey";
                correct +=1
                break;
            case false:
                popup_text[i].style.borderColor = "red"
                break;
        }
    }
    if (correct == 3) {
        item_update = popup_text[0].value + "-" + popup_text[1].value + "-" + popup_text[2].value
        update_lists(item_update)
    }
}


// Update complete and partial lists with selected elements
function update_lists(item_update) {
    if (complete.includes(current_elm)) {
        let i = complete.indexOf(current_elm)
        complete[i]["id"] = item_update
        }
    else if (partial.includes(current_elm)) {
        let i = partial.indexOf(current_elm)
        partial.splice(i, 1)
        current_elm["id"] = item_update
        complete.push(current_elm)
        draw_boxes([current_elm], "LawnGreen", context)
        }
    else {
        custom_box["id"] = item_update
        complete.push(custom_box)
    }
    let popup = document.getElementById("Popup");
    popup.classList.remove("show")
}


// loading screen
function start_loading() {
    document.getElementsByClassName('page-1')[0].style.display = 'none';
    document.getElementsByClassName('loading')[0].style.display = 'table';
}



