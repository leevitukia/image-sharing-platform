let usernameField = document.getElementById("username")

document.getElementById("userForm").addEventListener('submit', function(event) {
    let username = usernameField.value;
    if(username.length >= 35){
        showWarning("Your username exceeds the maximum length, please choose one that's shorter than 35 characters.");
        event.preventDefault();
        return false;
    }
    return true;
});

let originalColor = usernameField.style.backgroundColor;
usernameField.addEventListener('input', function(event) {
    let username = event.target.value;
    if(username.length >= 35){
        usernameField.style.backgroundColor = "rgb(255, 80, 80)"
    }
    else{
        usernameField.style.backgroundColor = originalColor;
    }
});