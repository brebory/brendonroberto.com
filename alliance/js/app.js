$(document).ready( function() {
	$('.ab-1').click( function(e) {
		$.scrollTo("#hp-2", 200, "swing");	
		e.preventDefault();
	});
	$('.ab-2').click( function(e) {
		$.scrollTo("#hp-3", 200, "swing");
		e.preventDefault();
	});
	$('.ab-3').click( function(e) {
		$.scrollTo("#hp-4", 200, "swing");
		e.preventDefault();
	});
	$('.ab-top').click( function(e) {
		$.scrollTo("#hp-0", 200, "swing");
		e.preventDefault();
	});
});
