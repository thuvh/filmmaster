function open_channel() {
    var ch=new goog.appengine.Channel(token);
    ch.open({
          'onmessage':function(m) {
               console.log(m.data);
               if(window.webkitNotifications) {
                   var notice = webkitNotifications.createNotification(settings.FULL_DOMAIN + '/static/favicon.ico', 'title', m.data);
                   notice.show();
                   setTimeout(function() {
                       notice.cancel();
                   }, 5000);
               }
          }, 
          'onopen':function(){
            console.log('opened')
          }
    });
}
function init_channel(username) {
    $.getScript('http://filmaster-tools.appspot.com/_ah/channel/jsapi', function() {
        $.getScript('http://filmaster-tools.appspot.com/request-token/?client_id=' + username, function() {
          console.log('channel scripts loaded');
          $(document).ready(open_channel);
        });
    });
}
