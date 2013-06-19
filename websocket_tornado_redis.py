import threading
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import redis
import pprint


# This is ugly but I did not want to create multiple files for a so trivial
# example.
TEMPLATE = """
<!DOCTYPE>
<html>
<head>
    <title>Sample test</title>
    <script type="text/javascript" src="http://code.jquery.com/jquery-1.4.2.min.js"></script>
</head>
<body>
    <h1>Hello world</h1>
    <form method='POST' action='./'>
        <textarea name='data' id="data"></textarea>
        <div><input type='submit'></div>
    </form>
    <div id="log"></div>
    <script type="text/javascript" charset="utf-8">
        $(document).ready(function(){
            
            $('form').submit(function(event){
                var value = $('#data').val();
                $.post("./", { data: value }, function(data){
                    $("#data").val('');
                });
                return false;
            });
            
            
            if ("WebSocket" in window) {
              var ws = new WebSocket("ws://192.168.19.128:8080/realtime/");
              ws.onopen = function() {};
              ws.onmessage = function (evt) {
                  var received_msg = evt.data;
                  var html = $("#log").html();
                  html += "<p>"+received_msg+"</p>";
                  $("#log").html(html);
              };
              ws.onclose = function() {};
            } else {
              alert("WebSocket not supported");
            }
        });
    </script>
</body>
</html>
"""


LISTENERS = []


def redis_listener():
    r = redis.Redis('192.168.19.128')
    p = r.pubsub()
    p.subscribe('test_realtime')
    for message in p.listen():
        for element in LISTENERS:
            element.write_message(message['data'])


class NewMsgHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(TEMPLATE)

    def post(self):
        data = self.request.arguments['data'][0]
        r = redis.Redis('192.168.19.128')
        r.publish('test_realtime', data)
        print(data);                

class WsHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        LISTENERS.append(self)
        pprint.pprint(LISTENERS)
    def on_message(self, message):
        pass

    def on_close(self):
        LISTENERS.remove(self)


settings = {
    'auto_reload': True,
}

application = tornado.web.Application([
    (r'/realtime/', WsHandler),
], **settings)


if __name__ == "__main__":
    threading.Thread(target=redis_listener).start()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8080)
    tornado.ioloop.IOLoop.instance().start()