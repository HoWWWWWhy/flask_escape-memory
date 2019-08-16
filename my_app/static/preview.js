const preview_box = document.querySelector(".js-preview-box");
const preview_image = document.querySelector(".js-file-field");

preview_image.onchange = (input) => {
    //console.log("onchange test");
    //console.log(input.target);
    if(input.target.files.length > 0) {
        const reader = new FileReader();
        //console.log(reader);
        reader.onload = (e) => {
            //console.log(e.target.result);
            preview_box.src = e.target.result;
 
        };        
        
        reader.readAsDataURL(input.target.files[0]);       
    }
};