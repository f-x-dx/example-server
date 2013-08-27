function renderCurrOrder(error, data) {
    clearFlash();
    $(".btn").removeAttr("disabled");
    if (error) {
        console.log(error);
        flash("Internal server error, please contact support", "error");
    }
    else {
        $("#cart").empty().append(data);
        attachRemoveHandler();
    }
}

function attachRemoveHandler() {
    $(".btn-remove").click(function () {
        $(".btn").attr("disabled", "disabled");
        var id = $(this).attr("id");
        var res = send('POST','/merchant/'+ merchantId + '/remove_item',
                       {"id": id}, {}, renderCurrOrder);
    });
}

function attachHandlers() {
    $(".btn-add").click(function () {
        $(".btn").attr("disabled", "disabled");
        var quantity = $(this).siblings("input").val();
        $(this).siblings("input").val("");
        var id = $(this).attr("id");
        var res = send('POST','/merchant/'+ merchantId + '/add_item',
                       {"id":id, "quantity": quantity}, {}, renderCurrOrder);
    });
    attachRemoveHandler();
}
$(document).ready(attachHandlers);
