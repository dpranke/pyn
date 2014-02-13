import pymeta_helper

from pyn_exceptions import PynException


def parse_ninja_file(host, path):
    if not host.exists(path):
        raise PynException("'%s' does not exist" % path)
    build_text = host.read(path)

    return parse_ninja_text(host, build_text)


def parse_ninja_text(host, build_text):
    try:
        d = host.dirname(host.path_to_module(__name__))
        parser = pymeta_helper.make_parser(host.join(d, 'ninja.pymeta'))
        return parser.parse(build_text)
    except Exception as e:
        raise PynException(str(e))
