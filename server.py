import gc

from everyclass.auth import create_app

app = create_app()
gc.set_threshold(0)
gc.freeze()

if __name__ == '__main__':
    print("You should not run this file. "
          "Instead, run in Docker or `uwsgi --ini deploy/uwsgi-local.ini` for consistent behaviour.")
