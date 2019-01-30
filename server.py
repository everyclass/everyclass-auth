import gc

from everyclass.auth import create_app

app = create_app()

# disable gc and freeze
gc.set_threshold(0)  # 700, 10, 10 as default
gc.freeze()

if __name__ == '__main__':
    # process_handle_queue = multiprocessing.Process(target=start_register_queue)
    # process_handle_queue.start()
    app.run(host='0.0.0.0')
