// project/static/js/auto_username.js
document.addEventListener("DOMContentLoaded", function () {
    let emailInput = document.getElementById("id_email");
    let usernameInput = document.getElementById("id_username");

    if (emailInput && usernameInput) {
        usernameInput.readOnly = true;  // make username not editable

        emailInput.addEventListener("input", function () {
            let emailVal = emailInput.value;
            if (emailVal.includes("@")) {
                let username = emailVal.split("@")[0];
                usernameInput.value = username;
            }
        });
    }
});

 