
// Setup jQuery so that we send and receive JSON objects instead of jQuery's
// application/x-www-form-urlencoded data.  We also use our own "extended JSON" which supports
// Dates.
//
// Also use cookie-to-header CSRF mitigation.


$.ajaxSetup({
  type: 'POST',
  contentType: 'application/json',
  converters: { 'text JSON': parseAndDecodeJSON },
  processData: false, // disable jQuery.param processing
});

var reCSRF = /(?:^|; )csrf=([^;]+)/;

$.ajaxPrefilter(function(options, originalOptions, jqXHR) {
  if (options.contentType === 'application/json' && typeof options.data === 'object') {
    options.data = JSON.stringify(encode(options.data));
  }

  var match = reCSRF.exec(document.cookie);
  if (match) {
    options.headers = { 'X-CSRF-Token': match[1] };
  }
});

function parseAndDecodeJSON(text) {
  var json = $.parseJSON(text);
  return decode(json);
}

// Adds a special encoding / decoding for Date objects designed to allow us to send anything we
// can use in a RethinkDB database with a browser.
//
// IMPORTANT: This does not handle or even look for cycles.  It will hang with 100% CPU usage
// if you do that!

function encode(obj) {
  // Cycle through all objects and convert Dates to JSON-compatible objects.

  var value;

  var queue = [ obj ];
  while (queue.length) {
    var current = queue.shift();

    if (Array.isArray(current)) {

      for (var i = 0, c = current.length; i<c; i++) {
        value = current[i];
        if (value) {
          if (value instanceof Date) {
            current[i] = { "$date$" : value.valueOf() };
          } else if (typeof value === 'object') { // object and array
            queue.push(value);
          }
        }
      }

    } else if (typeof current === 'object') {

      for (var prop in current) {
        if (current.hasOwnProperty(prop)) {
          value = current[prop];

          if (value) {
            if (value instanceof Date) {
              current[prop] = { "$date$" : value.valueOf() };
            } else if (typeof value === 'object') { // object and array
              queue.push(value);
            }
          }
        }
      }

    }

  } // while queue

  return obj;
}

function decode(obj) {
  // Cycle through all objects and convert $date$ and $id$ back to Date objects.

  var queue = [ obj ];

  while (queue.length) {

    var current = queue.shift();
    var value;

    if (Array.isArray(current)) {
      for (var i = 0, c = current.length; i<c; i++) {
        value = current[i];
        if (value) {
          if (Array.isArray(value)) {
            queue.push(value);
          } else if (typeof value === 'object') {
            if (value['$date$']) {
              current[i] = new Date(value['$date$']);
            } else {
              queue.push(value);
            }
          }
        }
      }
    } else if (typeof current === 'object') {
      // The outermost object itself can't be a date or id - we must always have a wrapper.
      for (var prop in current) {
        if (!current.hasOwnProperty(prop))
          continue;

        value = current[prop];

        if (value && typeof value === 'object') {
          if (Array.isArray(value)) {
            queue.push(value);
          } else {
            if (value['$date$']) {
              current[prop] = new Date(value['$date$']);
            } else {
              queue.push(value);
            }
          }
        }
      }
    }
  }

  return obj;
}
