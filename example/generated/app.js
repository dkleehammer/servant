
$(function() {
  var counter = 1;

  $('#test').on('click', function(e) {
    e.preventDefault();
    e.stopPropagation();

    $.ajax({
      url: '/click',
      data: {
        counter: counter,
        timestamp: new Date()
      },
      success: function(data) {
        counter = data.counter;
        $('#counter').text(counter);
        $('#timestamp').text(data.timestamp + ":" + typeof(data.timestamp));
      }
    });
  });
});
