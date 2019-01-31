import functools

from flask import abort, request

from everyclass.auth.config import get_config

config = get_config()


def json_payload(*fields, supposed_type=None, supposed_in=None):
    """
    装饰器，检查 MIME-type 是否为 json，并检查各个字段是否存在

    :param supposed_in: 如果指定了 `supposed_in`，检查字段是否在 `supposed_in` 内
    :param supposed_type: 如果指定了 `supposed_type`，检查各个字段的类型是否为 `supposed_type`
    """

    def decorator(func):
        @functools.wraps(func)
        def _wrapped(*args, **kwargs):
            if not request.json:
                return abort(400)
            for each_field in fields:
                if request.json.get(each_field) is None:
                    return abort(400)
                # 类型检查
                if supposed_type is not None and not isinstance(request.json.get(each_field), supposed_type):
                    return abort(400)
                # 区间检查
                if supposed_in is not None and request.json.get(each_field) not in supposed_in:
                    return abort(400)
            return func(*args, **kwargs)

        return _wrapped

    return decorator
