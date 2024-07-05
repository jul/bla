#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Licence : see license in package (

"""

LICENSE:
    GNU General Public License https://www.gnu.org/licenses/gpl.html

AUTHOR
    julien@tayon.net


"""
from ldap3 import Server, Connection
from ldap3.core.exceptions import LDAPCursorError
import ldap3
from collections.abc import MutableMapping
from subprocess import run as call

from time import time
from ldap3.utils.log import set_library_log_detail_level, ERROR
import re
from sys import argv
from os import environ as env
from pathlib import Path
from json import dumps
import inspect
import logging
from getpass import getpass

has_pygments = False
formater = lambda x: x

try:
    import pygments
    from pygments.formatters import TerminalFormatter as formater
    import pygments.lexers
    has_pygments = True
except:
    pass


GLOBAL_CONFIG = "/etc/bla.json"
USER_CONFIG = "~/.bla.json"
USER_SCRIPT=""
GLOBAL_LDAP_CONF = "/etc/ldap/ldap.conf"
SENTINEL = object()
CONFIG = dict()

# LDAP conf parser
parse_conf = lambda strg: re.findall(
        r'^(?P<key>[A-Z]+)\s+(?P<value>[^\s]+)\s?\n', 
        strg, re.M
)

try:
    CONFIG.update({
        k.lower(): v for k, v in parse_conf(open(GLOBAL_LDAP_CONF).read())
    })
    if "base" in CONFIG:
        CONFIG["search_base"] = CONFIG["base"]
except Exception:
    pass


def usage():
    print(__doc__)


def error(*a, **kw):
    usage()
    print("**** ERROR ****")
    print()
    print("%r,%r" % (a,kw))
    print()
    exit()



try:
    USER_CONFIG = argv[1]
    #print("file %s loaded" % USER_CONFIG)
except IndexError:
    pass

try:
    USER_SCRIPT = argv[2]
    #print("file %s loaded" % USER_CONFIG)
except IndexError:
    pass





def format_entry(e, alt_formater=SENTINEL, alt_format_opt=SENTINEL):
    """print beautified entry
    expect in %(USER_CONFIG)s a cli key with following values:
        - lexer (default ldif (json possible)) to tell what you prefer to see
        - format_opt given to the pygments.Ter
    if pygments is not installed will revert to json.dumps with indent=4
    """
    cfg = CONFIG.get("cli", {})
    lexer = cfg.get("lexer", "json")
    try:
        plexer = pygments.lexers.get_lexer_by_name(lexer)
        actual_formater = formater
        if alt_formater is not SENTINEL:
            actual_formater = alt_formater
        format_opt = alt_format_opt is not SENTINEL \
            and alt_format_opt \
            or cfg.get("format_opt", dict())
        return(pygments.highlight(
            getattr(e, "entry_to_%s" % lexer)(),
            plexer,
            actual_formater(**format_opt)
        ))
    except Exception:
        print("Check that you installed the pygment lexer for %s" % lexer)
    return e.entry_to_json()


def pe(e):
    """print beautified entry
    expect in %(USER_CONFIG)s a cli key with following values:
        - lexer (default ldif (json possible)) to tell what you prefer to see
        - format_opt given to the pygments.Ter
    if pygments is not installed will revert to json.dumps with indent=4
    """
    print(format_entry(e))


def get_serializer(suffix=".json"):
    suffix_to_module = dict({
        '.json': "json",
        '.yml': "yaml",
        '.yaml': "yaml",
    })
    kw_for_dump = dict(
        json=dict(indent=4),
        yaml=dict(default_flow_style=False),
    )
    module_name = None
    try:
        module_name = suffix_to_module[suffix]
    except KeyError:
        raise NotImplementedError(
                "The suffix for this file is not handled yet (%s)" % suffix)

    module = __import__(module_name, fromlist=[])
    loads = None
    for loader in ["safe_load", "safe_loads", "loads", "load"]:
        try:
            loads = getattr(module, loader)
            break
        except AttributeError:
            pass
    else:
        raise ImportError("Could not find a loader for (%s)" % suffix)

    dumps = None
    for dumper in ["safe_dumps", "dumps", "safe_dump", "dump"]:
        try:
            # python bug? (missing reraise?)
            dumpf = getattr(module, dumper)
            dumps = lambda a_dict: dumpf(
                    a_dict,
                    **kw_for_dump.get(module_name, {})
            )
            break
        except AttributeError:
            pass
    else:
        raise ImportError("Could not find a dumper for (%s)" % suffix)

    return loads, dumps


def load_config(filename=USER_CONFIG, ignore_missing=True, ignore_mode=False):
    filename = Path(filename).expanduser()
    #print("config %s loaded" % filename)
    if not filename.exists() and ignore_missing:
        return dict()
    mode = filename.stat().st_mode
    if (mode & 0x77):
        if ignore_mode:
            print(
                "** WARNING make sure no secrets are stored in (%s) : "
                "permission (%s) are too wide.**" % (
                    filename, oct(mode & 0o777))
            )
        else:
            raise OSError(
                "Permission too wide on %s (expected 0o600 found %s)" % (
                    filename, oct(mode & 0o777))
            )

    loads, _ = get_serializer(filename.suffix)
    return loads(filename.read_text())


def save_config(filename=USER_CONFIG, config=CONFIG, ignore_mode=False):
    if not isinstance(config, MutableMapping):
        raise ValueError(
            "Got a config of type %s expected a MutableMapping (dict)" % (
                type(config),
            ))
    filename = Path(filename).expanduser()
    _, dumps = get_serializer(filename.suffix)
    dbg(dumps)
    test_before_save = dumps(config)
    dbg(test_before_save)
    filename.parent.mkdir(0o0660, parents=True, exist_ok=True)
    filename.write_text(test_before_save)
    if not ignore_mode:
        # by default rights should be tight
        filename.chmod(0o600)

try:
    CONFIG.update({
        k.lower(): v for k, v in parse_conf(open(GLOBAL_LDAP_CONF).read())
    })
    if "base" in CONFIG:
        CONFIG["search_base"] = CONFIG["base"]
except Exception:
    pass

CONFIG.update(load_config(GLOBAL_CONFIG), ignore_missing=True)
CONFIG.update(load_config(USER_CONFIG), ignore_missing=True)


if "password" not in CONFIG and "user" in CONFIG:
    if env.get("PASSWORD"):
        print("password found in env['PASSWORD']")
        CONFIG["password"] = env["PASSWORD"]
    else:
        print("please enter password for %r" % CONFIG["user"])
        CONFIG["password"] = getpass()


if not CONFIG.keys() & {"host", "uri"}:
    error(
        "No configuration provided "
        "Cowardly refusing to guess"
        "\n"
        "check the existence of (%s, %s)" % (GLOBAL_LDAP_CONF, USER_CONFIG)
    )


def mlast(ldap_cx):
    print("\n".join([str(e.entry_dn) for e in ldap_cx.entries]))


def set_logging(filename=False):
    filename = filename or "bla.log." + str(time())
    logging.basicConfig(filename=filename, level=logging.DEBUG)
    print("ERROR LDAP logging  %s" % filename)
    set_library_log_detail_level(ERROR)


if CONFIG.get("logging"):
    set_logging(CONFIG["logging"])


def get_params_from_sig(a_func):
    sig = inspect.signature(a_func)
    pos = []
    keyword = []
    for par in sig.parameters.values():
        if par.default == par.empty:
            pos += [par.name, ]
        else:
            keyword += [par.name]
    keyword = set(keyword) - set(pos)
    return pos, keyword


class FallbackEntry(object):
    def __init__(self, entry, fallback):
        self.entry = entry
        self.fallback = fallback
        self.fallback["dn"] = entry.entry_dn

    def __getitem__(self, key):
        try:
            return self.fallback[key]
        except KeyError:
            return getattr(self.entry, key)


def get_default_config(
        method,
        realm=SENTINEL,
        global_conf=SENTINEL,
        epilogue=SENTINEL):
    """BUG (not really): double decoration gives weird results when
    a key has same name in 2 calls"""
    pos_d, keyword_d = get_params_from_sig(method)
    if global_conf is SENTINEL:
        global_conf = CONFIG.copy()
    _realm = realm
    if realm is SENTINEL:
        _realm = global_conf.copy()
    else:
        try:
            _realm = realm.copy()
            for k, v in _realm.items():
                    _realm[k] = v % global_conf
        except Exception:
            pass

    def wrapper(*a, **kw):
        dbg(method.__name__)
        nonlocal realm
        if realm is SENTINEL:
            _realm = global_conf.copy()
        else:
            _realm = realm.copy()
            dbg(global_conf)
            for k, v in _realm.items():
                try:
                    _realm[k] = v % global_conf
                except Exception:
                    pass
        dbg(_realm)
        new_pos = a
        dbg(new_pos)
        dbg(pos_d)
        keep = set(pos_d) - set(kw)
        dbg(keep)
        provided = keep | (set(kw) & set(pos_d))
        dbg(provided)
        # before : non know positionnal argument from sig (like self)
        # that are not in provided keywords un call
        # or values that can be subtituted
        key_before = [k for k in pos_d if k not in kw and k not in _realm]
        dbg(key_before)

        # subtitute positional arguments with defaults for values that
        # do not support defaults
        # their position is after before and must not override provided args
        # (rule is if positionnal argument provided they implicitly are at
        # the end of positional
        # ex ldap.search(dn, filter) => search(ldap_instace, dn, filter)
        # if 1 argument is provided it is filter
        before = a[:len(key_before)]
        dbg(before)
        offset_before = len(before)
        # keys in positional that must be provided and present in call
        # middle are all elements in pos_d intersect signature
        middle = new_pos[offset_before:]
        dbg(middle)
        new_pos_d = pos_d[offset_before:]
        dbg(new_pos_d)
        dbg(len(new_pos_d) - len(middle))

        new_middle = []
        if new_pos_d:
            dbg(new_pos_d[:len(new_pos_d) - len(middle)])
            new_middle = [
                _realm[elt] for elt in new_pos_d[:len(new_pos_d) - len(middle)]
            ]
        dbg(new_middle)

        after = provided and middle[-len(provided):] or []

        dbg(after)
        dbg("END P B M A")
        final_pos = list(before) + list(new_middle) + list(after)
        dbg(final_pos)
        keyword = {
            k: v for k, v in _realm.items() if k in set(keyword_d) - keep
        }
        dbg("KW B: %r" % kw)
        keyword.update({
            k: v for k, v in kw.items() if k not in pos_d or k in keep
        })
        dbg("KW A: %r" % keyword)
        res = method(*final_pos, **keyword)
        if epilogue is SENTINEL:
            return res
        else:
            return epilogue(res, *a, **kw)

    wrapper.__name__ = method.__name__
    wrapper.__doc__ = (method.__doc__ or "") + """

This function is having the following positionnal :
defaulted  : %s
And current default values are : %s """ % (
        pos_d or [], dumps(_realm or {}, indent=4)
    )
    return wrapper


def return_entries(res, ldap_cnx, *a, **kw):
    if res:
        ret = ldap_cnx.entries
        try:
            ret = [e.entry_writable() for e in ret]
        except LDAPCursorError:
            pass
        if CONFIG.get("cli", {}).get("show_entries"):
            for e in ret:
                pe(e)
        if len(ret) == 1:

            ret = ret.pop()
        return ret


class EasierLDAP(Connection):
    def __init__(self, *a, **kw):
        if not a or (a and type(a[0]) != ldap3.core.server.Server):
            new_server = Server(*a, **kw)
            new_pos = [new_server] + list(a)[1:]
        super().__init__(*new_pos, **kw)

    def get(self, dn):
            if not self.search(
                    search_base=dn,
                    search_filter='(objectClass=*)',
                    attributes=['+', '*'], search_scope="BASE"):
                return False
            this_entry = self.entries[0]
            assert(this_entry.entry_dn.lower() == dn.lower())
            return this_entry


def dft_dbg(a, msg=""):
    caller = inspect.getframeinfo(inspect.stack()[1][0])
    try:
        print("%s:%d - %s %s" % (
            caller.function,
            caller.lineno,
            msg and "(%s)" % msg,
            repr(a))
        )
    except Exception:
        pass

do_nothing = lambda *a, **kw: 42

dbg = 'call' in str(CONFIG.get("debug", "")) and dft_dbg or do_nothing

if not CONFIG.keys() & {"host", "uri"}:
    error(
        "No configuration provided "
        "Cowardly refusing to guess"
        "\n"
        "check the existence of (%s, %s)" % (GLOBAL_LDAP_CONF, USER_CONFIG)
    )


def msearch_ip(self, ip):
    if self.s("(aRecord=*)"):
        res = [e for e in self.entries if ip in str(e.aRecord)]
        if CONFIG.get("cli", {}).get("show_entries"):
            for e in res:
                pe(e)
        return res


mail_search = CONFIG.get("mail_search", dict(
    search_base="ou=People,%(search_base)s",
    search_filter="(uid=*)",
    attributes=["mail", "cn"],
    search_scope="LEVEL",
    epilogue=return_entries
))

dns_entry_search = CONFIG.get("dns_entry_search", dict(
    search_base="ou=hosts,%(search_base)s",
    search_scope="SUBTREE",
))

Connection.__init__ = get_default_config(Connection.__init__)
Connection.s = get_default_config(
    Connection.search,
    epilogue=return_entries,
)

Connection.search_mail = get_default_config(
    Connection.search, CONFIG.get("mail_search"),
    epilogue=return_entries,
)


Connection.search_host = lambda self, hostname, **kw: get_default_config(
    Connection.s,
    dns_entry_search,
    epilogue=return_entries,
    )(
        self,
        "(|(dc=%(host)s)(CNAMERecord=%(host)s)(associatedDomain=%(host)s))" % {
            "host":  hostname},
        **kw
    )


Connection.arecord = lambda self, hostname, **kw: get_default_config(
    Connection.s,
    dns_entry_search,
    )(self, "(aRecord=%s)" % hostname, **kw)


Connection.rptrecord = lambda self, hostname, **kw: get_default_config(
    Connection.s,
    dns_entry_search,
    )(self, "(RPTRRecord=%s)" % hostname, **kw)


Connection.search_ip = msearch_ip
Connection.last = mlast
Server.__init__ = get_default_config(Server.__init__, CONFIG.get("server", {}))
Server.__repr__ = Server.__string__ = lambda self: "Server (%d)" % id(self)
Connection.__repr__ = lambda self: "Connection (%d)" % id(self)


try:

    ldap = EasierLDAP(CONFIG["host"])
    # si ZZ necessaire, auto_bind va péter
    try:
        del(CONFIG["auto_bind"])
    except:
        pass
    if CONFIG.get("start_tls", "true"):
        ldap.start_tls()
    ldap.bind()

    def user_add(uid, **kw):
        max_def = lambda x, min_def=2000: max(list(map(
            lambda e: getattr(e, x).value,
            search("(%s=*)" % x, attributes=[x]))) + [min_def]
        )
        uidNumber = 2000
        try:
            uidNumber=max_def("uidNumber")+1
        except:
            pass
        gidNumber = 2000
        try:
            gidNumber=max_def("gidNumber")+1
        except:
            pass
        
        user_template = CONFIG.get(
                "user_template",
                dict(
                    object_class=[
                        'top', 'account', 'posixAccount', ],
                    attributes=dict(
                        loginShell="/bin/bash",
                        homeDirectory="/home/%s" % uid,
                        uidNumber=uidNumber,
                        uid=uid, cn=uid, gidNumber=gidNumber,
                        userPassword="{crypt}rien"
                    )
                )
            )

        ldap.add("uid=%s,ou=People,dc=home" % uid, **user_template)

    def walk(
            search_base=CONFIG["search_base"],
            emit=lambda e: e,
            filter=do_nothing,
    ):
        """ walk from given dn and descend into all entries.
        emit applies function to entry, returns results.
        filter serves as ... a filter
        """
        ldap.search(
            search_filter='(objectClass=*)',
            search_base=search_base,
            search_scope="LEVEL",
            attributes=['+', '*']
        )
        for e in ldap.entries:
            if filter(e):
                emit_me = emit(e)
                if emit_me:
                    yield emit_me

            yield from walk(
                    search_base=e.entry_dn,
                    filter=filter,
                    emit=emit,
            )

    def last():
        return ldap.entries

    def lp(e, *attrs, **changes):
        res = changes.get("dn", lambda x: x)(e.entry_dn) + "\n"
        for a in attrs:
            if a in e.entry_attributes:
                for v in getattr(e, a).values:
                    res += "%s: %s\n" % (
                        a, v.decode() if hasattr(v, "decode") else v ) # noqa
        return res

    def ldapvi(*what, **kw):
        identity = lambda v: v
        if len(what) == 1:
            what = what[0].split()
        what = list(what)
        translate = dict(
                sasl_mechanism=dict(key="--sasl-mech"),
                host=dict(key="-h"),
                # mouais
                #start_tls=dict(key="-Z", apply=lambda x: ""),
                user=dict(key="--user"),
                password=dict(key="--password"),
                search_base=dict(key="-b"),
                search_scope=dict(
                    key="-s",
                    apply=dict(
                            SUBTREE="sub",
                        BASE="base",
                        ONE="one",
                    ).get
                ),
        )
        options = list()
        for k in (set(CONFIG.keys()) | set(kw.keys())) & translate.keys():
            options += [
                translate[k]["key"], translate[k].get("apply", identity)(kw.get(k, CONFIG[k]))
            ]
        to_mask = kw.get("password", CONFIG.get("password"))
        call(["ldapvi"] + options + what)
        print("ldapvim was called with : ")
        print(" ".join(["ldapvi"] + [
            o if to_mask and o != to_mask else len(to_mask) * "*"
            for o in options] + what
        ))

    def test_attr(e, test_on_value, *attributes):
        return any(a in e.entry_attributes and test_on_value(getattr(e, a)) for a in attributes)  # noqa

    get = ldap.get
    search = ldap.s
    mail = ldap.search_mail

    host = ldap.search_host
    arecord = ldap.arecord
    ip = ldap.search_ip
    rptrecord = ldap.rptrecord
    mod_pwd = ldap.extend.standard.modify_password

    def password(user=None, newpass=None):
        pass1, pass2 = 1, 2
        user = user or CONFIG["user"]
        if not newpass:
            while pass1 != pass2:
                print("Veuillez entrer le mot de passe pour %s" % user)
                pass1 = getpass()
                pass2 = getpass()
            newpass = pass2
        print(mod_pwd(
            user or CONFIG.get("user"), new_password=newpass) and "OK" or "KO")
    
    pp = lambda s: dumps(s, indent=4, default=repr)
    if USER_SCRIPT:
        print(f"script detected executing : {USER_SCRIPT}")
        exec(open(USER_SCRIPT).read())

except Exception as e:
    print(e)
    print("Testing mode config not loaded")
