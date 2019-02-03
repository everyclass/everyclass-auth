from gevent import monkey

monkey.patch_all()

import gc
import gevent.pywsgi
from everyclass.auth import create_app

app = create_app()
gc.set_threshold(0)
# gc.freeze()

if __name__ == '__main__':
    gevent_server = gevent.pywsgi.WSGIServer(('', 80), app)
    gevent_server.serve_forever()
