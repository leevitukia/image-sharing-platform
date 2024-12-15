document.getElementById("file").hidden = true;
document.getElementById("fileLabel").hidden = false;
// makes the fancy image preview visible if the user has javacsript enabled, otherwise just shows the standard file selector

document.getElementById('file').addEventListener('change', function(event) {
const file = event.target.files[0];
const preview = document.getElementById('imagePreview');

if (file) {
    const reader = new FileReader(); 
    reader.onload = function(e) {
        preview.src = e.target.result;
    };
    reader.readAsDataURL(file);
}
});