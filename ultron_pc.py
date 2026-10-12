import json, os, socket, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, ctypes, time
from ctypes import wintypes

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, 'config.json')
DEFAULT_TOKEN = 'ULTRON-CHANGE-ME-7429'
DEFAULT_ACTIONS = {
    'music_play': {'label':'Música: Play/Pause', 'type':'media', 'value':'play_pause'},
    'music_next': {'label':'Música: Próxima', 'type':'media', 'value':'next'},
    'music_prev': {'label':'Música: Anterior', 'type':'media', 'value':'previous'},
    'vol_up': {'label':'Volume +', 'type':'volume', 'value':'up'},
    'vol_down': {'label':'Volume -', 'type':'volume', 'value':'down'},
    'vol_mute': {'label':'Silenciar', 'type':'volume', 'value':'mute'},
    'shortcut_copy': {'label':'Copiar (Ctrl+C)', 'type':'shortcut', 'value':'ctrl+c'},
    'shortcut_paste': {'label':'Colar (Ctrl+V)', 'type':'shortcut', 'value':'ctrl+v'},
    'shortcut_alt_tab': {'label':'Alternar janela', 'type':'shortcut', 'value':'alt+tab'},
    'shortcut_desktop': {'label':'Mostrar desktop', 'type':'shortcut', 'value':'win+d'},
    'open_spotify': {'label':'Abrir Spotify', 'type':'program', 'value':'spotify:'},
    'open_browser': {'label':'Abrir navegador', 'type':'program', 'value':'https://www.google.com'},
    'script_1': {'label':'Script 1', 'type':'script', 'value':''},
    'script_2': {'label':'Script 2', 'type':'script', 'value':''},
    'game_key': {'label':'Tecla de jogo (F1)', 'type':'shortcut', 'value':'f1'},
    'shortcut_f5': {'label':'Atualizar (F5)', 'type':'shortcut', 'value':'f5'},
}
VK = {'ctrl':0x11,'alt':0x12,'shift':0x10,'win':0x5B,'tab':0x09,'enter':0x0D,'space':0x20,'esc':0x1B,'backspace':0x08,'delete':0x2E,'up':0x26,'down':0x28,'left':0x25,'right':0x27,'home':0x24,'end':0x23,'f1':0x70,'f2':0x71,'f3':0x72,'f4':0x73,'f5':0x74,'f6':0x75,'f7':0x76,'f8':0x77,'f9':0x78,'f10':0x79,'f11':0x7A,'f12':0x7B}
for c in 'abcdefghijklmnopqrstuvwxyz': VK[c] = ord(c.upper())
for c in '0123456789': VK[c] = ord(c)
VK_MEDIA = {'play_pause':0xB3, 'next':0xB0, 'previous':0xB1, 'stop':0xB2}
VK_VOLUME = {'up':0xAF,'down':0xAE,'mute':0xAD}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH,'r',encoding='utf-8') as f: data=json.load(f)
            data.setdefault('token', DEFAULT_TOKEN); data.setdefault('port', 8765)
            data.setdefault('actions', {})
            for k,v in DEFAULT_ACTIONS.items(): data['actions'].setdefault(k, v.copy())
            return data
        except Exception: pass
    return {'token':DEFAULT_TOKEN, 'port':8765, 'actions':{k:v.copy() for k,v in DEFAULT_ACTIONS.items()}}

def save_config(data):
    with open(CONFIG_PATH,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)

def key_event(vk, up=False):
    if vk is None: return
    ctypes.windll.user32.keybd_event(vk, 0, 0x0002 if up else 0, 0)

def do_shortcut(value):
    parts=[p.strip().lower() for p in value.split('+') if p.strip()]
    if not parts: return
    keys=[]
    for p in parts:
        vk=VK.get(p)
        if vk is None and len(p)==1: vk=ord(p.upper())
        if vk is None: raise ValueError('Tecla não reconhecida: '+p)
        keys.append(vk)
    for vk in keys: key_event(vk)
    time.sleep(0.04)
    for vk in reversed(keys): key_event(vk, True)

def run_action(action):
    typ=action.get('type',''); val=action.get('value','').strip()
    if typ=='media':
        key_event(VK_MEDIA.get(val)); key_event(VK_MEDIA.get(val), True)
    elif typ=='volume':
        key_event(VK_VOLUME.get(val)); key_event(VK_VOLUME.get(val), True)
    elif typ=='shortcut': do_shortcut(val)
    elif typ=='program':
        if not val: raise ValueError('Configure o caminho/URL do programa primeiro.')
        if val.startswith('http://') or val.startswith('https://') or val.endswith(':'):
            os.startfile(val)
        else:
            os.startfile(os.path.expandvars(os.path.expanduser(val)))
    elif typ=='script':
        if not val: raise ValueError('Escolha um arquivo .bat, .cmd, .ps1 ou programa para este script.')
        path=os.path.expandvars(os.path.expanduser(val.strip('"')))
        if not os.path.isfile(path): raise ValueError('Arquivo não encontrado: '+path)
        ext=os.path.splitext(path)[1].lower()
        if ext in ('.bat','.cmd'): subprocess.Popen(['cmd.exe','/c',path], cwd=os.path.dirname(path) or None)
        elif ext=='.ps1': subprocess.Popen(['powershell.exe','-ExecutionPolicy','RemoteSigned','-File',path], cwd=os.path.dirname(path) or None)
        else: os.startfile(path)
    else: raise ValueError('Tipo de ação desconhecido.')

class Server:
    def __init__(self, app): self.app=app; self.sock=None; self.running=False
    def start(self):
        if self.running: return
        cfg=self.app.config
        try:
            self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM); self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            self.sock.bind(('0.0.0.0', int(cfg.get('port',8765)))); self.sock.listen(5); self.sock.settimeout(1)
            self.running=True; threading.Thread(target=self.loop,daemon=True).start(); self.app.set_status('Servidor ativo na porta '+str(cfg.get('port',8765)))
        except Exception as e:
            self.app.set_status('Erro ao iniciar: '+str(e)); self.stop()
    def stop(self):
        self.running=False
        try:
            if self.sock: self.sock.close()
        except: pass
        self.sock=None
    def loop(self):
        while self.running:
            try: conn, addr=self.sock.accept()
            except socket.timeout: continue
            except OSError: break
            threading.Thread(target=self.client,args=(conn,addr),daemon=True).start()
    def client(self, conn, addr):
        try:
            conn.settimeout(4); buf=b''
            while True:
                chunk=conn.recv(4096)
                if not chunk: break
                buf+=chunk
                while b'\n' in buf:
                    line,buf=buf.split(b'\n',1)
                    try:
                        msg=json.loads(line.decode('utf-8'))
                        if msg.get('token') != self.app.config.get('token'): raise PermissionError('Token incorreto')
                        aid=str(msg.get('action',''))
                        action=self.app.config.get('actions',{}).get(aid)
                        if not action: raise ValueError('Ação não configurada: '+aid)
                        run_action(action); response={'ok':True,'message':'Executado: '+action.get('label',aid)}
                        self.app.set_status('Comando recebido de '+addr[0]+': '+action.get('label',aid))
                    except Exception as e: response={'ok':False,'message':str(e)}
                    conn.sendall((json.dumps(response,ensure_ascii=False)+'\n').encode('utf-8'))
        except Exception: pass
        finally:
            try: conn.close()
            except: pass

def local_ips():
    ips=[]
    try:
        for info in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET):
            ip=info[4][0]
            if not ip.startswith('127.') and ip not in ips: ips.append(ip)
    except: pass
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('192.0.2.1',80)); ip=s.getsockname()[0]; s.close()
        if not ip.startswith('127.') and ip not in ips: ips.insert(0,ip)
    except: pass
    return ips or ['Verifique a conexão USB']

class App:
    def __init__(self, root):
        self.root=root; self.config=load_config(); self.server=Server(self)
        root.title('ULTRON Stream Deck — Controle do PC'); root.geometry('980x700'); root.minsize(820,560); root.configure(bg='#101014')
        style=ttk.Style(); style.theme_use('clam'); style.configure('TFrame',background='#101014'); style.configure('TLabel',background='#101014',foreground='#f2f2f2'); style.configure('TButton',padding=6); style.configure('TEntry',fieldbackground='#222229',foreground='#ffffff'); style.configure('TCombobox',fieldbackground='#222229')
        header=tk.Label(root,text='ULTRON  /  STREAM DECK',bg='#101014',fg='#ff3434',font=('Segoe UI',20,'bold')); header.pack(anchor='w',padx=18,pady=(14,2))
        tk.Label(root,text='Painel do PC • comandos autorizados pelo seu tablet',bg='#101014',fg='#a6a6b0',font=('Segoe UI',10)).pack(anchor='w',padx=20)
        top=ttk.Frame(root); top.pack(fill='x',padx=18,pady=12)
        self.ip_label=ttk.Label(top,text='IPs do PC: '+', '.join(local_ips())); self.ip_label.pack(side='left',fill='x',expand=True)
        ttk.Button(top,text='Atualizar IP',command=self.refresh_ip).pack(side='left',padx=4)
        self.start_btn=ttk.Button(top,text='Iniciar servidor',command=self.start_server); self.start_btn.pack(side='left',padx=4)
        ttk.Button(top,text='Parar',command=self.stop_server).pack(side='left',padx=4)
        security=ttk.Frame(root); security.pack(fill='x',padx=18,pady=(0,8))
        ttk.Label(security,text='Token de segurança:').pack(side='left')
        self.token_var=tk.StringVar(value=self.config.get('token',DEFAULT_TOKEN)); ttk.Entry(security,textvariable=self.token_var,width=34).pack(side='left',padx=8)
        ttk.Label(security,text='Porta:').pack(side='left',padx=(10,2)); self.port_var=tk.StringVar(value=str(self.config.get('port',8765))); ttk.Entry(security,textvariable=self.port_var,width=7).pack(side='left')
        ttk.Button(security,text='Salvar segurança',command=self.save_security).pack(side='left',padx=8)
        tk.Label(root,text='CONFIGURE CADA BOTÃO DO TABLET',bg='#101014',fg='#ff5555',font=('Segoe UI',11,'bold')).pack(anchor='w',padx=20,pady=(6,2))
        tk.Label(root,text='Escolha tipo e valor. Para programas/scripts, use o caminho do arquivo. O tipo “Atalho” aceita, por exemplo, ctrl+shift+esc ou f5.',bg='#101014',fg='#b7b7c1',wraplength=920,justify='left').pack(anchor='w',padx=20,pady=(0,8))
        outer=ttk.Frame(root); outer.pack(fill='both',expand=True,padx=18,pady=2)
        canvas=tk.Canvas(outer,bg='#101014',highlightthickness=0); scroll=ttk.Scrollbar(outer,orient='vertical',command=canvas.yview); self.rows_frame=ttk.Frame(canvas)
        self.rows_frame.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0,0),window=self.rows_frame,anchor='nw'); canvas.configure(yscrollcommand=scroll.set); canvas.pack(side='left',fill='both',expand=True); scroll.pack(side='right',fill='y')
        self.vars={}; self.build_rows()
        bottom=ttk.Frame(root); bottom.pack(fill='x',padx=18,pady=10)
        ttk.Button(bottom,text='Salvar configurações',command=self.save_all).pack(side='left')
        ttk.Button(bottom,text='Restaurar padrão',command=self.reset_defaults).pack(side='left',padx=8)
        self.status=tk.StringVar(value='Servidor parado. Conecte o tablet por USB e ative “Compartilhamento USB”.'); ttk.Label(root,textvariable=self.status).pack(anchor='w',padx=20,pady=(0,12))
        root.protocol('WM_DELETE_WINDOW',self.close)
    def build_rows(self):
        for w in self.rows_frame.winfo_children(): w.destroy()
        headers=['ID do botão','Nome exibido','Tipo','Valor / caminho']; widths=[18,23,15,50]
        for i,(h,w) in enumerate(zip(headers,widths)): tk.Label(self.rows_frame,text=h,bg='#1c1c24',fg='#ff6262',font=('Segoe UI',9,'bold'),width=w,anchor='w',padx=5,pady=6).grid(row=0,column=i,sticky='ew',padx=1,pady=1)
        self.vars={}
        for r,(aid,action) in enumerate(self.config['actions'].items(),1):
            label=tk.StringVar(value=action.get('label',aid)); typ=tk.StringVar(value=action.get('type','shortcut')); val=tk.StringVar(value=action.get('value',''))
            tk.Label(self.rows_frame,text=aid,bg='#15151b',fg='#dddddf',font=('Consolas',9),width=18,anchor='w',padx=5).grid(row=r,column=0,sticky='ew',padx=1,pady=1)
            tk.Entry(self.rows_frame,textvariable=label,bg='#222229',fg='white',insertbackground='white',relief='flat',width=23).grid(row=r,column=1,sticky='ew',padx=2,pady=2,ipady=5)
            ttk.Combobox(self.rows_frame,textvariable=typ,values=['media','volume','shortcut','program','script'],state='readonly',width=13).grid(row=r,column=2,sticky='ew',padx=2,pady=2)
            tk.Entry(self.rows_frame,textvariable=val,bg='#222229',fg='white',insertbackground='white',relief='flat',width=50).grid(row=r,column=3,sticky='ew',padx=2,pady=2,ipady=5)
            self.vars[aid]=(label,typ,val)
    def refresh_ip(self): self.ip_label.config(text='IPs do PC: '+', '.join(local_ips()))
    def set_status(self,msg): self.root.after(0,lambda:self.status.set(msg))
    def save_security(self):
        try: port=int(self.port_var.get()); assert 1<=port<=65535
        except: messagebox.showerror('Porta inválida','Informe uma porta entre 1 e 65535.'); return
        token=self.token_var.get().strip()
        if len(token)<8: messagebox.showerror('Token fraco','Use um token com pelo menos 8 caracteres.'); return
        was=self.server.running
        if was: self.server.stop()
        self.config['port']=port; self.config['token']=token; save_config(self.config)
        if was: self.server.start()
        self.set_status('Configuração de segurança salva.')
    def save_all(self):
        self.config['actions']={aid:{'label':v[0].get().strip() or aid,'type':v[1].get(),'value':v[2].get().strip()} for aid,v in self.vars.items()}
        self.save_security(); save_config(self.config); self.set_status('Configurações salvas em config.json.')
    def start_server(self): self.save_all(); self.server.start()
    def stop_server(self): self.server.stop(); self.set_status('Servidor parado.')
    def reset_defaults(self):
        if messagebox.askyesno('Restaurar','Restaurar os botões originais?'): self.config['actions']={k:v.copy() for k,v in DEFAULT_ACTIONS.items()}; self.build_rows(); self.save_all()
    def close(self): self.server.stop(); self.root.destroy()

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
