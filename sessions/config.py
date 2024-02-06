from ast import Attribute
from .validators import TypeOf, OneOf, Bool


class PackageConfig:
    __slots__ = (
        "_debug",
        "_semaphore",
        "_raise_errors",
        "_return_callbacks",
        "_run_callbacks_on_error",
        "_print_callback_exceptions",
        "_print_callback_tracebacks",
        "_threaded_timeout",
        "_renew_cache_on_get",
    )

    debug:                          Bool                    = Bool()
    semaphore:                      OneOf                   = OneOf("local", "global")
    raise_errors:                   Bool                    = Bool()
    return_callbacks:               Bool                    = Bool()
    run_callbacks_on_error:         Bool                    = Bool()
    print_callback_exceptions:      Bool                    = Bool()
    print_callback_tracebacks:      Bool                    = Bool()
    threaded_timeout:               TypeOf                  = TypeOf(int, float, None.__class__)
    renew_cache_on_get:             Bool                    = Bool()

    def __init__(
        self,
        debug:                      bool                    = False,
        semaphore:                  str                     = "local",
        raise_errors:               bool                    = True,
        return_callbacks:           bool                    = False,
        run_callbacks_on_error:     bool                    = False,
        print_callback_exceptions:  bool                    = True,
        print_callback_tracebacks:  bool                    = False,
        threaded_timeout:           int | float | None      = None,
        renew_cache_on_get:         bool                    = True,
    ):
        self.debug                                          = debug
        self.semaphore                                      = semaphore
        self.raise_errors                                   = raise_errors
        self.return_callbacks                               = return_callbacks
        self.run_callbacks_on_error                         = run_callbacks_on_error
        self.print_callback_exceptions                      = print_callback_exceptions
        self.print_callback_tracebacks                      = print_callback_tracebacks
        self.threaded_timeout                               = threaded_timeout
        self.renew_cache_on_get                             = renew_cache_on_get

    def __repr__(self):
        keys = tuple(key.lstrip('_') for key in self.__slots__)
        values = tuple(getattr(self, key) for key in self.__slots__)
        items = zip(keys, values)

        max_var_length = max(len(key) for key in keys)
        max_value_length = max(len(str(value)) for value in values)
        max_line_length = max_var_length + max_value_length + 4

        sep = "|"
        line_sep = sep + "-" * (max_line_length) + sep
        header = f"<Sessions Package Config>\n{line_sep}\n| field {sep:>{max_var_length - len('field') + 1}} value |\n{line_sep}"

        lines = [f"| {key} {sep:>{max_var_length - len(key) + 1}} {value}" for key, value in items]
        lines = [f"\n{line}{' ' * (max_line_length - len(line) + 1)}{sep}" for line in lines]

        return f"{header}{''.join(lines)}\n{line_sep}"


    def __str__(self):
        return repr(self)

    def set(self, key, value):
        if f"_{key}" in self.__slots__:
            return setattr(self, key, value)
        raise AttributeError(f"SessionConfig has no option: '{key}'")

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        if f"_{key}" in self.__slots__:
            return setattr(self, key, value)
        raise AttributeError(f"SessionConfig has no option: '{key}'")

    def __getattr__(self, __name: str):
       print(f"SessionConfig has no option: '{__name}'")

SessionConfig = PackageConfig()