# sys.ftp_conn

St = sys.static()
Dy = sys.dynamic()
all = Dy.list('ftp_conn')

def init():
    # Kill old connections
    for i in all[:]:
        if i: i.comm_close()

    del all[:]

class ftp_conn(sys.conn.conn):
    fsm = St.ftp_fsm

    def __init__(S, x):
        all.append(S)
        St._dirty = 1
        S.player = None

    def comm_close(S):
        all.remove(S)
        if S.player: S.player.set_ftp(None)
        sys.conn.conn.comm_close(S)

    def auth(S, line):
        arg1, arg2 = string.split(line)
        arg1 = string.lower(arg1)
        if not re.search('^[a-z]+$', arg1): return 'close'
        try:
            S.player = mud.player.instance(arg1)
            if S.player.pwd != arg2: return 'close'
            S.player.set_ftp(S)
            return 'welcome'
        except db.NoSuchObject: return 'close'

    def waitpush(S, line):
        if line != 'PUSH': return 'perror'
        else: return 'push'

    def idle(S, line):
        if line == 'NOOP': return 'noop'
        else: return 'error'

    def edit(S, s, co, cf):
        if S.state != 'idle': raise RuntimeError, 'mudftp connection busy'
        l = string.split(str, '\n')
        s = string.join(l, '\n')
        if not str: l = '\n'
        S.write('SENDING %s %d %s\n%s\n' % (`id(str)`, len(l), `hash(str)`,str))
        S.co = co
        S.cf = cf
        S.state = 'send'   # bypass tostate

    def send(S, l):
        args = string.split(l)
        if args[0] != 'PUT': return 'error'
        try: S.left = eval(args[2], { '__builtins__': None })
        except: return 'error'
        S.lines = []
        return 'recv'
    
    def recv(S, l):
        S.lines.append(l)
        S.left = S.left - 1
        if S.count <= 0:
            # Ugh. We can't persist function references. This basically does S.cbobj(string.join(lines, '\n'))
            s = string.join(S.lines, '\n') + '\n'
            apply(getattr(S.co, S.cf), [s])
            S.write("OK %s\n" % `hash(s)`)
            return 'idle'
        else: return 'recv'
	
