


var InputPass = document.getElementById("Inputpass");
var eye = document.getElementById("eye")
var eyeH = document.getElementById("eyeH")
var btn_sign_in = document.getElementById("btnIn");
var btn_sign_up = document.getElementById("btnUp");
var container = document.getElementById("contain")
var container_welcom = document.getElementById("container-welcom")


eyeH.addEventListener("click", e =>{
    if(InputPass.type === "password"){
      InputPass.type = "text";     
      eyeH.style.display ="none";
      eye.style.display ="flex";
    }
  });
  eye.addEventListener("click", e =>{
    if(InputPass.type === "text"){
      InputPass.type = "password";
      eye.style.display ="none";
      eyeH.style.display ="flex";
    }
  });

btn_sign_in.addEventListener("click", ()=>{
 container.classList.toggle("toggle")
});
btn_sign_up.addEventListener("click", ()=>{
  container.classList.remove("toggle")
 });

eye.addEventListener("click", function () {
    if (Input.type == "password") {
        Input.type = "Text";
    } else {
        Input.type = "password";
    };
});



//document.addEventListener('DOMContentLoaded', function() {
    const carouselItems = document.querySelectorAll('.carousel-item');
    const totalItems = carouselItems.length;
    let currentIndex = 0;
  
    function goToItem(index) {
      if (index < 0 || index >= totalItems) return;
  
      carouselItems.forEach(item => {
        item.style.transform = `translateX(-${index * 100}%)`;
      });
  
      currentIndex = index;
    }
  
    document.querySelector('.carousel-control.prev').addEventListener('click', function() {
      goToItem(currentIndex - 1);
    });
  
    document.querySelector('.carousel-control.next').addEventListener('click', function() {
      goToItem(currentIndex + 1);
    });
