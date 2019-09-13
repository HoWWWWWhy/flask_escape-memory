const preview_box = document.querySelector(".js-preview-box");
const preview_image = document.querySelector(".js-file-field");

/*
preview_image.onchange = (input) => {
    //console.log("onchange test");
    //console.log(input.target);
    const files = input.target.files;
    if(files.length > 0) {
        const reader = new FileReader();
        //const file = files[0];
        //console.log(file);
        reader.onload = (e) => {
            //console.log(e.target.result);
            preview_box.src = e.target.result;
 
        };        
        
        reader.readAsDataURL(input.target.files[0]);       
    }
};
*/

//for Heroku & AWS S3

preview_image.onchange = (input) => {

    const files = input.target.files;

    if(files.length > 0) {
        const file = files[0]; 
        getSignedRequest(file);//for Heroku & AWS S3    
    }
    else {
        return alert("No file selected.");
    }
};

function getSignedRequest(file){
    
    const xhr = new XMLHttpRequest();
    
    xhr.open("GET", "/sign_s3?file_name="+file.name+"&file_type="+file.type);// 요청 초기화
    xhr.onreadystatechange = function(){
      console.log(xhr.readyState);
      if(xhr.readyState === 4){
        if(xhr.status === 200){
          const response = JSON.parse(xhr.responseText);   
          console.log(response.data);
          console.log(response.url);        
          uploadFile(file, response.data, response.url);

        }
        else{
          alert("Could not get signed URL.");
        }
      }
    };
    xhr.send();
}

function uploadFile(file, s3Data, url){
    const xhr = new XMLHttpRequest();
    
    console.log(s3Data);
    let postData = new FormData();
    for(key in s3Data.fields){
      postData.append(key, s3Data.fields[key]);
    }
    postData.append('file', file);
    console.log(postData.get("signature"));
    console.log(postData.get("file"));
    console.log(xhr);
    
    xhr.onreadystatechange = function() {
      console.log(xhr.readyState);
      if(xhr.readyState === 4){
        if(xhr.status === 200 || xhr.status === 204){
            preview_box.src = url;
          //document.getElementById("avatar-url").value = url;
        }
        else{
          alert("Could not upload file.");
        }
          
     }
    };
    console.log(postData);
    xhr.open("POST", s3Data.url);
    xhr.send(postData);// upload to s3
    console.log("send!");
}
