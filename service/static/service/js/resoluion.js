function get_resolution(){
   var w = window.innerWidth;
   var h = window.innerHeight;
    
   var x = document.getElementById("demo");
   x.innerHTML = "Browser width: " + w + ", height: " + h + ".";
   return  x.innerHTML
}
