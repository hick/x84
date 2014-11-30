#coding=utf-8
"""
Hick 定制的登录以后的画面(配置文件 ~/.x84/default.ini 中替换 x84 默认的 top)
"""
__author__  = "Hick"
__license__ = 'MIT'
__email__   = 'hickwu@gmail.com'

import logging
import time
import os

# local
from x84.bbs import getterminal, showart, echo, ini
from x84.bbs import getsession, get_user, User, LineEditor
from x84.bbs import getch, goto, gosub, DBProxy, syncterm_setfont
from x84.default.common import coerce_terminal_encoding
from ConfigParser import Error as ConfigError

def refresh():
    """ 显示主菜单"""
    logger = logging.getLogger()
    session, term = getsession(), getterminal()
    session.activity = u'Main menu'
    ### 读取的 ascii art 文件
    artfile = 'hick.asc'
    echo(u''.join((
        u'\r\n',
        term.blue(u'/'.rjust(term.width / 2)), term.bold_black(u'/ '),
        term.bold('x'), term.bold_blue('/'), term.bold('84'), u' ',
        u'主菜单',
        u'\r\n')))
    # displays a centered main menu header in topaz encoding for utf8
    for line in showart(os.path.join(os.path.dirname(__file__),'art',artfile),'topaz'):
        echo(term.cyan+term.move_x((term.width/2)-40)+line)
    echo(u'\r\n')
    ### 下面是主菜单
    entries = [
        ('$', u'查看公告'),
        ('b', u'站点穿梭'),
        # ('l', 'ASt CAllS'),
        # ('o', 'NE liNERS'),
        ('w', u"在线用户"),
        ('n', u'新闻列表'),
        # ('c', u'聊天室'),
        # ('i', u'IRC聊天'),
        ('!', u"编码调整\n"),
        ('t', u'测试调试'),
        # ('s', 'YS. iNfO'),
        # ('u', 'SER LiST'),
        # ('f', 'ORECASt'),
        ('e', u'个人资料'),
        ('p', u'发表文章'),
        ('r', u'查看消息'),
        # ('v', 'OTiNG bOOTH'),
        ('g', u'离开本站'),]

    # add LORD to menu only if enabled: dosemu 模块后边了解下， 暂时保留
    if ini.CFG.getboolean('dosemu', 'enabled') and (
            ini.CFG.get('dosemu', 'lord_path') != 'no'):
        entries.insert(0, ('#', 'PlAY lORd!'))

    # add sesame doors to menu if enabled
    if ini.CFG.has_section('sesame'):
        from ConfigParser import NoOptionError
        for door in ini.CFG.options('sesame'):
            if '_' in door:
                continue

            # .. but only if we have the binary
            if not os.path.exists(ini.CFG.get('sesame', door)):
                continue

            # .. and a key is configured
            try:
                key = ini.CFG.get('sesame', '{}_key'.format(door))
            except NoOptionError:
                logger.error("no key configured for sesame door '{}'".format(
                    door,
                ))
            else:
                logger.debug("added sesame door '{}' with key '{}'".format(
                    door, key
                ))
                entries.insert(0, (key, 'PlAY {}'.format(door)))

    ### 渲染输出主菜单
    buf_str = u''
    for key, name in entries:
        out_str = u''.join((
            term.bold(u'('),
            term.bold_blue_underline(key),
            term.bold(u')'),
            term.bold_blue(name.split()[0]),
            u' ', u' '.join(name.split()[1:]),
            u'  '))
        ansilen = term.length(buf_str + out_str)
        if ansilen >= (term.width * .8):
            echo(term.center(buf_str) + u'\r\n\r\n')
            buf_str = out_str
        else:
            # 每行换行
            echo(term.center(buf_str) + u'\r\n\r\n')
            buf_str = out_str

    echo(term.center(buf_str) + u'\r\n\r\n')
    echo(u' [%s]:' % (
        term.blue_underline(''.join([key for key, name in entries]))))


def login(session, user):
    """
    登记登录用户---没有改操作后边会处理为匿名
    Assign ``user`` to ``session`` and return time of last call.

    performs various saves and lookups of call records
    """
    session.user = user

    # assign timeout preference
    timeout = session.user.get('timeout', None)
    if timeout is not None:
        session.send_event('set-timeout', timeout)

    # update call records
    user.calls += 1
    user.lastcall = time.time()

    # save user record
    if user.handle != u'anonymous':
        user.save()

    # update 'lastcalls' database
    lc_db = DBProxy('lastcalls')
    with lc_db:
        previous_call, _, _ = lc_db.get(user.handle, (0, 0, 0,))
        lc_db[user.handle] = (user.lastcall, user.calls, user.location)

    return previous_call


def get_user_record(handle):
    """
    根据 handle 参数(最前面的 matrix  传递过来的)获得用户信息
    Find and return User class instance by given ``handle``.

    If handle is ``anonymous``, Create and return a new User object.
    """
    log = logging.getLogger(__name__)

    if handle == u'anonymous':
        log.debug('anonymous login'.format(handle))
        return User(u'anonymous')

    log.debug('login by {0!r}'.format(handle))
    return get_user(handle)

def main(handle=None):
    """ 主体程序"""
    session, term = getsession(), getterminal()
    session.activity = 'hick'

    ### 处理登录
    # attempt to coerce encoding of terminal to match session.
    coerce_terminal_encoding(term, session.encoding)

    # fetch user record
    user = get_user_record(handle)

    # register call
    login(session, user)

    session = getsession()

    ### 处理键盘操作事件
    inp = -1
    dirty = True
    while True:
        if dirty or session.poll_event('refresh'):
            refresh()
        inp = getch(1)
        dirty = True
        if inp == u'*':
            goto('main')  # reload main menu using hidden option '*'
        elif inp == u'$':
            gosub('bulletins')
        elif inp == u'b':
            gosub('bbslist')
        elif inp == u'l':
            gosub('lc')
        elif inp == u'o':
            gosub('ol')
        elif inp == u's':
            gosub('si')
        elif inp == u'u':
            gosub('userlist')
        elif inp == u'w':
            gosub('online')
        elif inp == u'n':
            gosub('news')
        elif inp == u'f':
            gosub('weather')
        elif inp == u'e':
            gosub('profile')
        elif inp == u'#':
            gosub('lord')
        ### 修改成
        elif inp == u't':
            gosub('feeds')
        elif inp == u'c':
            gosub('chat')
        elif inp == u'i':
            gosub('ircchat')
        elif inp == u'p':
            gosub('writemsg')
        elif inp == u'r':
            gosub('readmsgs')
        elif inp == u'v':
            gosub('vote')
        elif inp == u'g':
            goto('logoff')
        elif inp == u'!':
            gosub('charset')
        elif inp == '\x1f' and 'sysop' in session.user.groups:
            # ctrl+_, run a debug script
            gosub('debug')
        else:
            handled = False
            try:
                for option in ini.CFG.options('sesame'):
                    if option.endswith('_key'):
                        door = option.replace('_key', '')
                        key = ini.CFG.get('sesame', option)
                        if inp == key:
                            gosub('sesame', door)
                            handled = True
                            break
            except ConfigError:
                pass

            if not handled:
                dirty = False
