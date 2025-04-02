var original= 1000;
function checkbalance(){
    alert(`Your current balance is ${original}`);
}
function deposit(){
    const deposit= document.getElementById("deposit_amount").value;
    original= original + parseInt(deposit);
}
function withdraw(){
    const withdraw= document.getElementById("withdraw_amount").value;
    if(withdraw<=original){
        original= original - parseInt(withdraw);
        alert(`${withdraw} has been withdrawn from your account. New balance is: ${original}`);
    }else{
        alert("Insufficient balance");
    }

}
function numberonly(input)
{   
    var num = /[^0-9]/gi;//field which is allowed in that particular input field
    input.value=input.value.replace(num,"");//replaces characters other than number with a space or blank 
    //short hand but above one is easy to understand
    //input.value = value.replace(/[^0-9]/g, '');

    var number = document.getElementById("deposit_amount").value;
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