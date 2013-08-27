var Utils = {
    renderFieldErrorTooltip: function (selector, msg, placement) {
        var elem;
        if (typeof placement === 'undefined') {
            placement = 'right'; // default to right-aligned tooltip
        }
        elem = $(selector);
        elem.tooltip({'title': msg, 'trigger': 'manual', 'placement': placement});
        elem.tooltip('show');
        elem.addClass('error');
        elem.on('focus click', function(e) {
            elem.removeClass('error');
            elem.tooltip('hide');
        });
    }
};

function send(method, url, params, data, callback) {
    var getParams = $.map(params, function(val, key) {
        return encodeURIComponent(key)+'='+encodeURIComponent(val);
    });

    if (getParams.length) {
        url += '?' + getParams.join('&');
    }

    var config = {type: method,
                  success: function(data) {
                      callback(null, data);
                  },
                  error: function(error) {
                      callback(error, null);
                  }};

    if (method.toLowerCase() == 'post') {
        config.data = JSON.stringify(data);
        config.contentType = "application/json; charset=UTF-8";
    }
    $.ajax(url, config);
}

function flash(message, category, clear) {
    $('#maincontent').prepend('<div class="alert alert-' + category + '"> '+
                              '<a class="close" data-dismiss="alert">×</a>'+
                              message + '</div>');
}

function clearFlash() {
    $('#maincontent .alert').remove();
}
