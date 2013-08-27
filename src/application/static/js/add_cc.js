
function nextpage(error, data){
    if(error){
        $("#cc_div").removeClass("loading");
        $("body").removeClass("loading");
    }
    else {
        window.location = '/customer_home';
    }
}

var merchant_id;
var last_four;

function callback() {

    if(merchant_id == undefined || last_four == undefined) {
        flash("Something went wrong. Please try again.", "error");
    }
    else if(response == undefined || response.result == undefined) {
        flash("Server Timeout. Please try again.");
    } else if (response.result == "DECLINED") {
        flash("Credit Card Declined", "error");
    } else if (response.result == "APPROVED") {
        var obj = {"paytoken": response.token,
            "merchant": merchant_id,
            "last_four":last_four};
    } else {
        var obj = {"paytoken": "invalid_token",
            "merchant": merchant_id,
            "last_four":last_four};
    }
    send("POST", '/post_cc', {}, obj, nextpage);
}

function sendscript() {
    if($("#name").val() == null ||
       $("#name").val() == ""){
        alert("Please enter the name on the card.");
        return false;
    }
    else if($("#credit_card").val().length <= 12 ||
            ! /^\d+$/.test($("#credit_card").val())){
        alert("Invalid Credit Card number. Please check to make sure it is "+
                "entered correctly.");
        return false;
    }
    else if($("#cvv").val().length != 3 ||
            ! /^\d+$/.test($("#cvv").val())){
        alert("Invalid cvv. Please make sure it is entered correctly.");
        return false;
    }
    else if($("#zip").val().length != 5 ||
            ! /^\d+$/.test($("#zip").val())){
        alert("Please enter the zip listed on your credit card.");
        return false;
    }
    merchant_details = $("#merchant").val().split(",");
    var n = merchant_details[0];
    var e = merchant_details[1];
    merchant_id = merchant_details[2];
    var prefix = merchant_details[3];
    var access_token = merchant_details[4];

    setKey(n, e)
    var credit_card = $("#credit_card").val().toString()
    last_four = credit_card.substring(credit_card.length - 4);

    $("#cc_div").addClass("loading");
    $("body").addClass("loading");
    sendInfo( credit_card, $("#name").val(), $("#cvv").val(), $("#zip").val(), 
                $("#month").val(), $("#year").val(), merchant_id, order.amount,
                order.orderId, prefix, access_token, callback);
    credit_card = "";
}
