# Workarounds to allow flask-caching to work with flask-restful
# Original code:
#   Copyright (c) 2010 by Thadeus Burgess.
#   Copyright (c) 2016 by Peter Justin.

from collections import OrderedDict
from flask_caching import Cache, get_arg_names, get_arg_default, iteritems, \
    function_namespace


class ResourceCache(Cache):
    def _memoize_version(self, f, args=None, reset=False, delete=False,
                         timeout=None, forced_update=False):
        """Updates the hash version associated with a memoized function or
        method.
        """
        # We don't care about which instance we're using for this
        fname, _ = function_namespace(f, args=args)
        version_key = self._memvname(fname)
        fetch_keys = [version_key]

        # Only delete the per-instance version key or per-function version
        # key but not both.
        if delete:
            self.cache.delete_many(fetch_keys[-1])
            return fname, None

        version_data_list = list(self.cache.get_many(*fetch_keys))
        dirty = False

        if callable(forced_update) and forced_update() is True:
            # Mark key as dirty to update its TTL
            dirty = True

        if version_data_list[0] is None:
            version_data_list[0] = self._memoize_make_version_hash()
            dirty = True

        # Only reset the per-instance version or the per-function version
        # but not both.
        if reset:
            fetch_keys = fetch_keys[-1:]
            version_data_list = [self._memoize_make_version_hash()]
            dirty = True

        if dirty:
            self.cache.set_many(dict(list(zip(fetch_keys, version_data_list))),
                                timeout=timeout)

        return fname, ''.join(version_data_list)

    def _memoize_kwargs_to_args(self, f, *args, **kwargs):
        #: Inspect the arguments to the function
        #: This allows the memoization to be the same
        #: whether the function was called with
        #: 1, b=2 is equivalent to a=1, b=2, etc.
        new_args = []
        arg_num = 0

        # If the function uses VAR_KEYWORD type of parameters,
        # we need to pass these further
        kw_keys_remaining = list(kwargs.keys())
        arg_names = get_arg_names(f)
        args_len = len(arg_names)

        for i in range(args_len):
            arg_default = get_arg_default(f, i)
            if i == 0 and arg_names[i] in ('self', 'cls'):
                # We specifically skip these self/cls cases since flask-restful
                # does not provide these to us anyway:
                # https://github.com/flask-restful/flask-restful/issues/585
                # If that ever changes, this should be updated.
                #arg_num += 1
                continue
            elif arg_names[i] in kwargs:
                arg = kwargs[arg_names[i]]
                kw_keys_remaining.pop(kw_keys_remaining.index(arg_names[i]))
            elif arg_num < len(args):
                arg = args[arg_num]
                arg_num += 1
            elif arg_default:
                arg = arg_default
                arg_num += 1
            else:
                arg = None
                arg_num += 1

            new_args.append(arg)

        return tuple(new_args), OrderedDict(sorted(
            (k, v) for k, v in iteritems(kwargs) if k in kw_keys_remaining
        ))
