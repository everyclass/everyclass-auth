import gc
from everyclass.auth import create_app

app = create_app()
gc.set_threshold(0)
gc.freeze()

if __name__ == '__main__':
    app.run(port=5000)

    # gevent_server = gevent.pywsgi.WSGIServer(('', 80), app)
    # gevent_server.serve_forever()
