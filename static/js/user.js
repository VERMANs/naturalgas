window.onload = function () {
    document.getElementById("user_name").setAttribute("readOnly", true);
};

function ToChange(id) {
    obj = document.getElementById(id);
    obj.readOnly = false;
}
