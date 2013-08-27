// Button handlers

function attach_handlers() {
  $("#link-merchant-btn").click(function () {
      window.location.href = "";
  });
}

$(document).ready(function() {
	attach_handlers();
	//update navbar
	$('.navbar').removeClass('cust').addClass('merch')
	$('.navbar li a').removeClass('active')
	$('.merchant-nav').addClass('active')
});
