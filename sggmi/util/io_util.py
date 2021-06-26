import warnings

def alt_open(*args, **kwargs):
    return open(*args, encoding="utf-8-sig", **kwargs)


def alt_print(*args, **kwargs):
    config = kwargs.pop("config")
    if config.echo:
        return print(*args, **kwargs)
    if config.log:
        tlog = (
            config.logs_dir
            / f"temp-{config.logs_prefix}{thetime()}{config.logs_suffix}"
        )
        with alt_open(tlog, "w") as temp_file:
            print(file=temp_file, *args, **kwargs)

        with alt_open(tlog, "r") as temp_file:
            data = temp_file.read()

        tlog.unlink()
        return config.logger.info(data)


def alt_warn(message, **kwargs):
    config = kwargs.pop("config")
    
    if config.log and config.echo:
        config.logger.warning(message)
    else:
        warnings.warn(message, stacklevel=2)

    #alt_print(message, config=config)


def alt_input(*args, **kwargs):
    config = kwargs.pop("config")

    if config.echo:
        if config.input:
            return input(*args)
        print(*args)
        return kwargs.get("default", None)

    if config.log:
        tlog = (
            config.logs_dir
            / f"temp-{config.logs_prefix}{thetime()}{config.logs_suffix}"
        )
        with alt_open(tlog, "w") as temp_file:
            print(file=temp_file, *args, **kwargs)

        with alt_open(tlog, "r") as temp_file:
            data = temp_file.read()

        tlog.unlink()
        return config.logger.info(data)

        if config.input:
            return input()

        return kwargs.get("default", None)


def alt_exit(code=None, config=None):
    alt_input("Press ENTER/RETURN to end program...", config=config)
    exit(code)
