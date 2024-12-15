const fileElement = document.getElementById("file");
const descriptionElement = document.getElementById("description");
const descriptionLength = document.getElementById("descriptionLength");
fileElement.hidden = true;
fileElement.required = false;
descriptionLength.style.display = "flex";
document.getElementById("fileLabel").hidden = false;
// makes the fancy image preview visible if the user has javacsript enabled, otherwise just shows the standard file selector

const preview = document.getElementById('imagePreview');
const container = document.getElementById("uploadImage");

document.getElementById("imageForm").addEventListener('submit', function(event) {
  let attached = fileElement.value !== '';
  let description = descriptionElement.value;
  if(!attached){
    showWarning("Please select an image to upload");
    event.preventDefault();
    return false;
  }
  else if(description.length > 300){
    showWarning("Your description is too long, please keep it below 300 characters");
    event.preventDefault();
    return false;
  }
  return true;
}); 

const originalColor = descriptionElement.style.backgroundColor;
descriptionElement.addEventListener('input', function(event) {
    const description = event.target.value;
    if(description.length >= 300){
        descriptionElement.style.backgroundColor = "rgb(255, 80, 80)"
    }
    else{
        descriptionElement.style.backgroundColor = originalColor;
    }
    descriptionLength.innerText = `${description.length}/300`
});

let image = new Image();
document.getElementById('file').addEventListener('change', function(event) {
const file = event.target.files[0];


if (file) {
    const reader = new FileReader(); 
    reader.onload = function(e) {
        image.src = e.target.result;
        preview.src = e.target.result;
        image.onload = function(){  
          const w = 70;
          const h = 45;
          const viewportAspectRatio = w / h;
          const imageAspectRatio = image.width / image.height;

          let width = `${w}vh`;
          let height = `${h}vh`;
          

          if(imageAspectRatio <= viewportAspectRatio){
            width = `${h * imageAspectRatio}vh`;
          }
          else{
            height = `${w / imageAspectRatio}vh`;
          }
          container.style.height = height;
          container.style.width = width;
          preview.style.height = height;
          preview.style.width = width;
        };
    };
    reader.readAsDataURL(file);
}
});