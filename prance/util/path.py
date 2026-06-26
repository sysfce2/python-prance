"""This module contains code for accessing values in nested data structures."""

__author__ = "Jens Finkhaeuser"
__copyright__ = "Copyright (c) 2018 Jens Finkhaeuser"
__license__ = "MIT"
__all__ = ()

_DICT_LIST = (dict, list)


def _json_ref_escape(path):
    """JSON-reference escape object path."""
    path = str(path)  # Could be an int, etc.
    path = path.replace("~", "~0")
    path = path.replace("/", "~1")
    return path


def _str_path(path):
    """Stringify object path."""
    return "/" + "/".join([_json_ref_escape(p) for p in path])


def _value_or_default(obj, defaultvalue):
    if obj is not None:
        return obj
    if defaultvalue is not None:
        return defaultvalue
    return obj


def path_get(obj, path, defaultvalue=None, path_of_obj=()):
    """
    Retrieve the value from obj indicated by path.

    Like dict.get(), except:

      - Any Mapping or Sequence is supported.
      - Path is itself a Sequence; the first part is applied to the passed
        object, the second part to the value returned from this operation, and
        so forth recursively.

    :param mixed obj: The Sequence or Mapping from which to retrieve values.
    :param Sequence path: A Sequence of zero or more key/index elements.
    :param mixed defaultvalue: If the value at the path does not exist and this
      parameter is not None, it is returned. Otherwise an error is raised.
    """
    if path is None or len(path) == 0:
        return _value_or_default(obj, defaultvalue)

    for key in path:
        if type(obj) not in _DICT_LIST:
            return _path_get_abc(obj, path, defaultvalue, path_of_obj)
        if type(obj) is dict:
            if key not in obj:
                raise KeyError(
                    'Object at "{}" does not contain key: {}'.format(
                        _str_path(path_of_obj), key
                    )
                )
            path_of_obj = path_of_obj + (key,)
            obj = obj[key]
        else:
            try:
                idx = int(key)
            except (ValueError, TypeError):
                raise KeyError(
                    'Sequence at "%s" needs integer indices only, but got: %s'
                    % (_str_path(path_of_obj), key)
                )
            if idx < 0 or idx >= len(obj):
                raise IndexError(
                    'Index out of bounds for sequence at "%s": %d'
                    % (_str_path(path_of_obj), idx)
                )
            path_of_obj = path_of_obj + (key,)
            obj = obj[idx]

    return _value_or_default(obj, defaultvalue)


def _path_get_abc(obj, path, defaultvalue=None, path_of_obj=()):
    """Fallback path_get for non-dict/list types using ABC checks."""
    from collections.abc import Mapping, Sequence

    if path is not None and not isinstance(path, Sequence):
        raise TypeError(f"Path is a {type(path)}, but must be None or a Collection!")

    if isinstance(obj, Mapping):
        if path is None or len(path) < 1:
            return _value_or_default(obj, defaultvalue)
        if path[0] not in obj:
            raise KeyError(
                'Object at "{}" does not contain key: {}'.format(
                    _str_path(path_of_obj), path[0]
                )
            )
        return _path_get_abc(
            obj[path[0]], path[1:], defaultvalue, path_of_obj + (path[0],)
        )
    elif isinstance(obj, Sequence):
        if path is None or len(path) < 1:
            return _value_or_default(obj, defaultvalue)
        try:
            idx = int(path[0])
        except ValueError:
            raise KeyError(
                'Sequence at "%s" needs integer indices only, but got: %s'
                % (_str_path(path_of_obj), path[0])
            )
        if idx < 0 or idx >= len(obj):
            raise IndexError(
                'Index out of bounds for sequence at "%s": %d'
                % (_str_path(path_of_obj), idx)
            )
        return _path_get_abc(
            obj[idx], path[1:], defaultvalue, path_of_obj + (path[0],)
        )
    else:
        if path is not None and len(path) > 0:
            raise TypeError(f"Cannot get anything from type {type(obj)}!")
        return _value_or_default(obj, defaultvalue)


def _fill_sequence(seq, index, path, path_index):
    """Fill a list with None until *index* is reachable, then append a typed placeholder."""
    if len(seq) > index:
        return
    while len(seq) < index:
        seq.append(None)
    next_index = path_index + 1
    if next_index < len(path) and type(path[next_index]) is int:
        seq.append([])
    elif next_index >= len(path):
        seq.append(None)
    else:
        seq.append({})


def path_set(obj, path, value, **options):
    """
    Set the value in obj indicated by path.

    Setter anologous to path_get() above.

    As setting values is a write operation, this function optionally creates
    intermediate objects to ensure all elements of path can be dereferenced.

    :param mixed obj: The Sequence or Mapping from which to retrieve values.
    :param Sequence path: A Sequence of zero or more key/index elements.
    :param mixed value: The value to set.
    :param bool create: [optional] Flag indicating whether to create
      intermediate values or not. Defaults to False.
    """
    create = options.get("create", False)

    if len(path) < 1:
        raise KeyError("Cannot set with an empty path!")

    root = obj
    last = len(path) - 1

    for i in range(last):
        key = path[i]
        if type(obj) not in _DICT_LIST:
            return _path_set_abc(root, path, value, create=create)
        if type(obj) is dict:
            if key not in obj:
                if not create:
                    raise KeyError(f'Key "{key}" not in Mapping!')
                next_key = path[i + 1]
                obj[key] = [] if type(next_key) is int else {}
            obj = obj[key]
        else:
            try:
                idx = int(key)
            except (ValueError, TypeError):
                raise KeyError("Sequences need integer indices only.")
            if create:
                _fill_sequence(obj, idx, path, i)
                if obj[idx] is None:
                    next_key = path[i + 1]
                    obj[idx] = [] if type(next_key) is int else {}
            obj = obj[idx]

    final = path[last]
    if type(obj) not in _DICT_LIST:
        return _path_set_abc(root, path, value, create=create)
    if type(obj) is dict:
        if not create and final not in obj:
            raise KeyError(f'Key "{final}" not in Mapping!')
        obj[final] = value
    else:
        try:
            idx = int(final)
        except (ValueError, TypeError):
            raise KeyError("Sequences need integer indices only.")
        if create:
            _fill_sequence(obj, idx, path, last)
        obj[idx] = value

    return root


def _path_set_abc(obj, path, value, create=False):
    """Fallback path_set for non-dict/list types using ABC checks."""
    from collections.abc import Sequence, MutableSequence, Mapping, MutableMapping

    if path is not None and not isinstance(path, Sequence):
        raise TypeError(f"Path is a {type(path)}, but must be None or a Collection!")

    if len(path) < 1:
        raise KeyError("Cannot set with an empty path!")

    if isinstance(obj, Mapping):
        if not isinstance(obj, MutableMapping):  # pragma: nocover
            raise TypeError(f"Mapping is not mutable: {type(obj)}")
        if len(path) == 1:
            if not create and path[0] not in obj:
                raise KeyError(f'Key "{path[0]}" not in Mapping!')
            obj[path[0]] = value
        else:
            if create and path[0] not in obj:
                if type(path[1]) == int:
                    obj[path[0]] = []
                else:
                    obj[path[0]] = {}
            _path_set_abc(obj[path[0]], path[1:], value, create=create)
        return obj

    elif isinstance(obj, Sequence):
        if not isinstance(obj, MutableSequence):
            raise TypeError(f"Sequence is not mutable: {type(obj)}")
        try:
            idx = int(path[0])
        except ValueError:
            raise KeyError("Sequences need integer indices only.")
        if create:
            _fill_sequence(obj, idx, path, 0)
        if len(path) == 1:
            obj[idx] = value
        else:
            _path_set_abc(obj[idx], path[1:], value, create=create)
        return obj
    else:
        raise TypeError(f"Cannot set anything on type {type(obj)}!")
