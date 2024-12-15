const imageElement = document.getElementById("postImg");
let image = new Image();
image.onload = function(){
    const w = 60;
    const h = 60;
    const viewportAspectRatio = w / h;
    const imageAspectRatio = image.width / image.height;
    console.log(imageAspectRatio);
    let width = `${w}vh`;
    let height = `${h}vh`;


    if(imageAspectRatio <= viewportAspectRatio){
        width = `${h * imageAspectRatio}vh`;
    }
    else{
        height = `${w / imageAspectRatio}vh`;
    }
    imageElement.style.width = width;
    imageElement.style.height = height;
    document.getElementById("commentsBox").style.maxHeight = height;
}
image.src = imageElement.src;