// This file contains the fucnctions called when running the application

//Library import from node
const { ipcRenderer } = require("electron")
const fs = require('fs');

// Starts camera feed
function start_camera(){
    video = document.getElementById('webcam');
    take_image_btn = document.getElementById('take_img_btn')
    navigator.mediaDevices.getUserMedia({
         video: {
            width: { ideal: 4096 }, // TODO Ideal camera resolution is 4k, can be adjusted 
            height: { ideal: 2160 } 
         }, 
         audio: false 
        })
    .then((stream) => {
        video.srcObject = stream;
        video.play();
        take_image_btn.style.display = "inherit"
        let mediaStreamTrack = stream.getVideoTracks()[0];
        imageCapture = new ImageCapture(mediaStreamTrack);
    })
    .catch((err) => {
      console.error(`An error occurred: ${err}`);
    });
}

// stops camera
function stop_camera() {
    video.pause()
}

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
    imageCapture.takePhoto()
    .then(blob => {
        saveBlob(blob)
    })
    ipcRenderer.on("SAVED_FILE", (event, path) => {
        start_loading()
        process_image({"path":"./temp/temp.png"})
    })
}


//Saves a blob as a photo
function saveBlob(blob) {
    let reader = new FileReader()
    reader.onload = function() {
        if (reader.readyState == 2) {
            var buffer = new Buffer.from(reader.result)
            ipcRenderer.send("SAVE_FILE", "./temp/temp.png", buffer)
        }
    }
    reader.readAsArrayBuffer(blob)
}



// Formating the image with the data from the backend to highlight the detected casettes and sets up the canvas
function format_image(image, data_list) {
    let canvas = document.getElementById('canvas');
    context = canvas.getContext('2d');
    img = document.createElement("img");
    img.src = String(image["path"])
    img.onload = function(){
        image_upscale = 1.5 // this is upscaler set in the python bakcend
        canvas.width = img.width*image_upscale
        canvas.height = img.height*image_upscale
        context.drawImage(img, 0, 0, img.width*image_upscale, img.height*image_upscale);
        // Rezise canvas to fit screen
        resizer = Math.floor(canvas.height/800) + 1 // Divide by  to resize // TODO Format for new camera
        canvas.style.height = canvas.height/resizer + "px"
        // Iterate over the data from the backend, the correctly identified ones
        complete = data_list[0] // fully identified entries
        draw_boxes(complete, "LawnGreen", context)
        // Iterate over the data from the backend, the partially identified ones
        partial = data_list[1] // partially identified entries
        draw_boxes(partial, "yellow", context)
        //adds sidebar
        update_sidebar(complete, partial)
        // sets up for cusom drawn boxes
        current_elm = ""
        custom_box = ""

        //add the ability to click on the rectang
        canvas.addEventListener('click', function (event) {
            let x = event.pageX - canvas.offsetLeft;
            let y = event.pageY - canvas.offsetTop;
            search_box(complete, x, y, resizer)
            search_box(partial, x, y, resizer)
        });

    //initialize overlay
    init_overlay()
    
    // Remove loading screen and display image once listeners and canvas has finished loading
    document.getElementsByClassName('loading')[0].style.display = 'none';
    document.getElementById('canvas').style.display = 'inline';
    document.getElementsByClassName('image')[0].style.display = 'block';
    check_partial(partial)
    }
}

// Sets up the overlay for custom user drawings
function init_overlay() {
        // listen for mouse held down
        var MouseIsDown = false;

        // Create overlay to draw on to avoid reseting the canvas
        overlay = document.getElementById("overlay");
        overlay.width = canvas.width
        overlay.height = canvas.height
        overlay.style.height = canvas.height/resizer + "px" 
        ovleray_ctx = overlay.getContext("2d")
        ovleray_ctx.strokeStyle = "LawnGreen";
        ovleray_ctx.lineWidth = 15;

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
                    custom_height = 0
                    custom_width = 0
                    current_elm = ""
                    MouseIsDown = true;
                    canvas.style.position = "absolute"
                    overlay.style.display = "inline"
                } 
            }
        });

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
            if (custom_height == 0 && custom_width == 0) {
                MouseIsDown = false
                canvas.style.position = "relative"
                overlay.style.display = "none"
            }
            if (MouseIsDown) {
                MouseIsDown = false;
                custom_box = {
                    "left": custom_startX,
                    "top": custom_startY,
                    "width": custom_width,
                    "height": custom_height
                }
                let popup = document.getElementById("Popup");
                let popup_text = document. getElementsByClassName("popuptext");
                popup.style.left = ((custom_startX/resizer) + ((custom_width/resizer)/2) + canvas.offsetLeft) +"px";
                popup.style.top = ((custom_startY/resizer) + canvas.offsetTop) + "px";
                popup_text[0].value = ""
                popup_text[1].value = ""
                popup_text[2].value = ""
                popup.classList.add("show");
                let undo = document.getElementById("remove_temp_rect")
                undo.style.display = "inline"
            }
        });
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
                let del = document.getElementById("remove_perm_rect");
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
                del.style.display = "inline"
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
        return true
    }
    return false
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
        check_partial(partial)
        }
    else {
        draw_boxes([custom_box], "LawnGreen", context)
        custom_box["id"] = item_update
        complete.push(custom_box)
        let undo = document.getElementById("remove_temp_rect")
        undo.style.display = "none"
        canvas.style.position = "relative"
        overlay.style.display = "none"
    }
    let popup = document.getElementById("Popup");
    popup.classList.remove("show")
    let del = document.getElementById("remove_perm_rect");
    del.style.display = "none"
    update_sidebar(complete, partial)
}

// Removes a temporary drawn rectangle 
function remove_temp_rect(){
    let popup = document.getElementById("Popup");
    popup.classList.remove("show")
    let undo = document.getElementById("remove_temp_rect")
    undo.style.display = "none"
    canvas.style.position = "relative"
    overlay.style.display = "none"
    let popup_text = document. getElementsByClassName("popuptext");
    popup_text[0].style.borderColor = "dimgrey";
    popup_text[1].style.borderColor = "dimgrey";
    popup_text[2].style.borderColor = "dimgrey";
    ovleray_ctx.clearRect(0, 0, overlay.width, overlay.height);
}


// Removes a permantn rectangle
function remove_perm_rect() {
    let popup = document.getElementById("Popup");
    popup.classList.remove("show")
    let popup_text = document. getElementsByClassName("popuptext");
    let del = document.getElementById("remove_perm_rect");
    del.style.display = "none"
    popup_text[0].style.borderColor = "dimgrey";
    popup_text[1].style.borderColor = "dimgrey";
    popup_text[2].style.borderColor = "dimgrey";
    // remove current elm from complete or partial
    if (complete.includes(current_elm)) {
        let i = complete.indexOf(current_elm)
        complete.splice(i, 1)
        }
    else if (partial.includes(current_elm)) {
        let i = partial.indexOf(current_elm)
        partial.splice(i, 1)
        check_partial(partial)
        }
    redraw_canvas()
    update_sidebar(complete, partial)
}


//redrawn canvas
function redraw_canvas() {
    context.drawImage(img, 0, 0, img.width*image_upscale, img.height*image_upscale);
    draw_boxes(complete, "LawnGreen", context)
    draw_boxes(partial, "yellow", context)
}

// loading screen
function start_loading() {
    stop_camera()
    document.getElementsByClassName('page-1')[0].style.display = 'none';
    document.getElementsByClassName('loading')[0].style.display = 'table';
}

//Checks if partial list is empty
function check_partial(partial) {
    if (partial.length == 0) {
        let status =  document.getElementById("status").value
        let archive_location =  document.getElementById("archive_location").value
        if (status == "Archiveing" && archive_location == "") {
            document.getElementById("submit").style.backgroundColor = "rgb(10, 73, 102)"
            document.getElementById("submit").onclick = function() {} 
            return false
        }
        document.getElementById("submit").style.backgroundColor = "rgb(22, 158, 221)"
        document.getElementById("submit").onclick = function() { submit(); } 
        return true
    }
    return false
}

//submits the results and restarts the page
function submit() {
    write_to_file(complete)
    //TODO: Should idealy push complete list to database instead of writing to file
    //window.open("index.html","_self")
}

// This is the window onload function, it starts scripts that launch when the page is opened
window.onload = function() {
    start_camera()
}


//Updates the display of complete and partial cassettes
function update_sidebar(complete, partial) {
    // Retritve and empty lists
    let doc_complete = document.getElementById("complete")
    let doc_partial =  document.getElementById("partial")
    doc_complete.innerHTML = ""
    doc_partial.innerHTML = ""
    let docs = [doc_complete, doc_partial]
    let lists = [complete, partial]
    for (i=0; i < 2; i++) {
        //sort the lists
        let sorted = lists[i].sort(function(a, b) {
            a.id = a.id.toUpperCase()
            b.id = b.id.toUpperCase()
            return (a.id < b.id) ? -1 : (a.id > b.id) ? 1 : 0;
        })
        //Add list Id's to display
        for (j=0; j < sorted.length; j++) {
            let li = (document.createElement("li"))
            let id = sorted[j]["id"]
            li.appendChild(document.createTextNode(id))
            li.onclick = function() {set_and_higlight(id)}
            docs[i].appendChild(li)
        }
    }
}


// Highligts all cassettes that fulfuill search requiremnts
function highlight_cassette(complete, partial) {
    redraw_canvas()
    let search_input = document.getElementById("search_inp").value
    search_input = search_input.replace(/ /g,"-");
    let found = []
    for (i=0; i < complete.length; i++) {
        if (complete[i]["id"].includes(search_input.toUpperCase())) {
            found.push(complete[i])
        }
    }
    for (i=0; i < partial.length; i++) {
        if (partial[i]["id"].includes(search_input.toUpperCase())) {
            found.push(partial[i])
        }  
    }
    draw_boxes(found, "OrangeRed", context)
}


// Sets the search value and searches
function set_and_higlight(search_term) {
    document.getElementById("search_inp").value = search_term
    highlight_cassette(complete, partial)
}


//Divides image into a 3x3 grid and returns which part the cassette is located in
function get_grid_location(cassette) {
    let location = ""
    //Finds it it's north or south by seeing if it's smaller or larger than 1 or 2 thirds of the image height
    if ((cassette["top"] + (cassette["height"]/2)) <=  (img.height*image_upscale)/3) {
        location =  "North"
    } else if ((cassette["top"] + (cassette["height"]/2)) >= (((img.height*image_upscale)/3)*2)) {
        location =  "South"
    }
    //Finds it it's west or east by seeing if it's smaller or larger than 1 or 2 thirds of image width
    if ((cassette["left"] + (cassette["width"]/2)) <=  (img.width*image_upscale)/3) {
        location = location + "West"
    } else if ((cassette["left"] + (cassette["width"]/2)) >= (((img.width*image_upscale)/3)*2)) {
        location = location + "East"
    }
    //If location is empty cassette is in the middle
    if (location.length == 0) {
        location =  "Middle"
    }
    return location
}


//Cheks if status is set to archiving
function check_archive() {
    let status =  document.getElementById("status").value
    let archive_location = document.getElementById("archive_location")
        if (status == "Archiveing") {
            archive_location.style.display="inline"
        }
        else {
            archive_location.style.display="none"
        }
    check_partial(partial)
}

//Temproary way of storing and oupting data whilst waiting for DataBase to be establihed
function write_to_file(complete) {
    for (i=0; i < complete.length; i++) {
        let unique_key = complete[i]["id"]
        let [id_case, sample_id, sample_type] = unique_key.split("-")
        let image_location = get_grid_location(complete[i])
        let status =  document.getElementById("status").value
        if (status == "Archiveing") {
            let archive_location =  document.getElementById("archive_location").value
            status = status + "_" + archive_location
        }
        let date = new Date()
        let local_time = date.toLocaleTimeString()
        let local_date = date.toISOString().split('T')[0];
        let ISO_timestamp = date.toISOString()
        //Writes down: Uniqe key, case id, sample id, type, cassette locationn in image, time, date(YY-MM-DD), ISO timestamp, staus
        let output = {
            "unique_key" : unique_key,
            "case _id" : id_case,
            "sample_id" : sample_id,
            "sample_type" : sample_type,
            "image_location" : image_location,
            "local_time" : local_time,
            "local_date" : local_date,
            "iso_timestamp" : ISO_timestamp,
            "stauts" : status
        }
        JSON_output = JSON.stringify(output) + "\n"
        fs.appendFile('./Output/OutputData.JSON', JSON_output, err => {
            if (err) {
              console.error(err);
            }
        });
    }
}

