let index = 0;
const slides = document.querySelectorAll(".carousel-slide");
const totalSlides = slides.length;

function showSlide(n) {
  index = (n + totalSlides) % totalSlides;
  document.querySelector(".carousel-container").style.transform = `translateX(${-index * 100}%)`;
}

function moveSlide(n) {
  showSlide(index + n);
}

function autoSlide() {
  moveSlide(1);
}

setInterval(autoSlide, 4000);

async function logout() {
  document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  try {
      const response = await fetch("/logout", {
          method: "POST",
          headers: {
              "Content-Type": "application/json"
          }
      });
      if (!response.ok) {
          throw new Error(`Logout failed: ${response.statusText}`);
      }
  } catch (err) {
      console.error("Error logging out:", err);
  }
  window.location.href = "/login";
}
function numberonly(input)
{   
    var num = /[^0-9]/gi;//field which is allowed in that particular input field
    input.value=input.value.replace(num,"");//replaces characters other than number with a space or blank 
    //short hand but above one is easy to understand
    //input.value = value.replace(/[^0-9]/g, '');

    var number = document.getElementById("number").value;
    var number_text = document.getElementById("verify_number");
    var numlength = number.length;
    let a = 10;

    if(numlength != (a) && numlength != 0)
    {
        number_text.innerHTML = "Please Enter 10 digit Phone-Number"
        number_text.style.color = "#ff0000";
    }
    else{
        number_text.innerHTML ="Valid 10 digit Phone-Number"
        number_text.style.color = "#00ff00";
    }
    //if the phone section is empty
    if (number == ""){
        number_text.innerHTML = "";
    }
}

//this function for alphabets only
function alphabetonly(input)
{
    var alpha = /[^a-zA-z]/gi;// gi is a flags that tells the function to look for match over the entire string (will otherwise break at the first match), this is the "g" flag. And the "i" flag tells it to match case insensitively.
    input.value=input.value.replace(alpha,"");    // Remove any non-alphabetic characters
    //short hand
    //input.value = value.replace(/[^a-zA-Z]/g, '');
}

//this function is to verify email
function verifyemail(){
    //var form = document.getElementById("form")
    var email = document.getElementById("email").value;
    var text = document.getElementById("verify_email");
    var pattern = /^[a-zA-Z0-9._%+-]+@gmail\.com$/;

    if (email.match(pattern))
    {
        text.innerHTML = "Your Email Address is valid";
        text.style.color = "#00ff00";
    }
    else{
        text.innerHTML = "Please enter valid Email Address";
        text.style.color = "#ff0000";
    }
    //if the email section is empty
    if (email== "") {
        text.innerHTML = "";      
    }
}