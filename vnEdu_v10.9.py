import tkinter as tk
from tkinter import ttk, messagebox

# --- 1. DỮ LIỆU HỆ THỐNG ---
mon_hoc = {
    "Toán học": "score", "Ngữ văn": "score", "Tiếng Anh": "score",
    "Âm nhạc": "check", "Mĩ thuật": "check",
    "KHTN": "score", "Lịch sử & Địa lý": "score", "GDCD": "score",
    "Công nghệ": "score", "Tin học": "score",
    "GD Thể chất": "check", "HĐ Trải nghiệm": "check", "Nội dung địa phương": "check"
}

alias_mon = {
    "t": "Toán học", "v": "Ngữ văn", "anh": "Tiếng Anh",
    "n": "Âm nhạc", "h": "Mĩ thuật", "kh": "KHTN",
    "sd": "Lịch sử & Địa lý", "cd": "GDCD",
    "cn": "Công nghệ", "tin": "Tin học",
    "gdtc": "GD Thể chất", "tn": "HĐ Trải nghiệm", "dp": "Nội dung địa phương"
}

data = {}
for mon, loai in mon_hoc.items():
    data[mon] = {
        "Kỳ 1": {"TX": [0.0], "GK": 0.0, "CK": 0.0, "status": "đạt", "loai": loai},
        "Kỳ 2": {"TX": [0.0], "GK": 0.0, "CK": 0.0, "status": "đạt", "loai": loai}
    }

system_locked = False 

def tinh_tb_mon(m):
    if m["loai"] == "check": return m["status"]
    tx = sum(m["TX"]); n = len(m["TX"])
    if n == 0: return 0
    return round((tx + m["GK"]*2 + m["CK"]*3) / (n + 5), 1)

# --- 2. GIAO DIỆN CHÍNH ---
class VnEduMobileUI:
    def __init__(self, root):
        self.root = root
        self.root.title("vnEdu Mobile v10.8")
        self.root.geometry("400x750")
        self.root.configure(bg="#f4f7f6")
        
        self.main_container = tk.Frame(self.root, bg="#f4f7f6", highlightbackground="#2980b9", highlightthickness=2)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        self.main_menu()

    def main_menu(self):
        for widget in self.main_container.winfo_children(): widget.destroy()
        header = tk.Frame(self.main_container, bg="#2980b9", pady=25)
        header.pack(fill=tk.X)
        tk.Label(header, text="VN-EDU MOBILE", font=("Arial", 20, "bold"), fg="white", bg="#2980b9").pack()

        btn_frame = tk.Frame(self.main_container, bg="#f4f7f6", pady=40)
        btn_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Button(btn_frame, text="XEM BẢNG ĐIỂM", bg="#27ae60", fg="white", font=("Arial", 13, "bold"), height=2, bd=0, command=self.check_lock).pack(fill=tk.X, padx=40, pady=12)
        tk.Button(btn_frame, text="SỬA ĐIỂM (ADMIN)", bg="#e67e22", fg="white", font=("Arial", 13, "bold"), height=2, bd=0, command=self.login_admin).pack(fill=tk.X, padx=40, pady=12)
        tk.Button(btn_frame, text="THOÁT ỨNG DỤNG", bg="#c0392b", fg="white", font=("Arial", 13, "bold"), height=2, bd=0, command=self.root.destroy).pack(fill=tk.X, padx=40, pady=40)

    def check_lock(self):
        if system_locked:
            lock_win = tk.Toplevel(self.root)
            lock_win.attributes('-fullscreen', True)
            lock_win.configure(bg="white")
            blue_bar = tk.Frame(lock_win, bg="#0084ff", height=60)
            blue_bar.pack(fill=tk.X)
            tk.Label(blue_bar, text="Kết quả học tập", font=("Arial", 16, "bold"), fg="white", bg="#0084ff", pady=15).pack()
            content = tk.Frame(lock_win, bg="white", padx=20, pady=40)
            content.pack(fill=tk.BOTH, expand=True)
            msg = "Thông báo: Hiện tại trường đang khóa tra cứu SLL, vui lòng liên hệ với Quản trị của nhà trường để biết thêm chi tiết."
            tk.Label(content, text=msg, font=("Arial", 16, "bold"), fg="#d63031", bg="white", wraplength=350, justify="left").pack(pady=20)
            tk.Button(lock_win, text="ĐÓNG", bg="#636e72", fg="white", font=("Arial", 12), command=lock_win.destroy).pack(pady=20, padx=50, fill=tk.X)
        else:
            self.view_all_scores()

    def login_admin(self):
        login = tk.Toplevel(self.root); login.geometry("320x320")
        tk.Label(login, text="XÁC THỰC", font=("Arial", 12, "bold"), pady=15).pack()
        pw_entry = tk.Entry(login, show="*", justify="center", font=("Arial", 18))
        pw_entry.pack(pady=10, padx=30, fill=tk.X); pw_entry.focus_set()
        
        def check(e=None):
            v = pw_entry.get().lower().strip()
            if v == "123": login.destroy(); self.edit_panel()
            elif v == "cmd": login.destroy(); self.terminal_mode()
            else: login.destroy()
        pw_entry.bind('<Return>', check)
        tk.Button(login, text="VÀO", bg="#2980b9", fg="white", command=check).pack(pady=10)

    def view_all_scores(self):
        top = tk.Toplevel(self.root)
        top.attributes('-fullscreen', True)
        header_f = tk.Frame(top, bg="#f4f7f6")
        header_f.pack(fill=tk.X)
        tk.Label(header_f, text="BẢNG ĐIỂM CHI TIẾT", font=("Arial", 18, "bold"), pady=20).pack()
        cols = ("mon", "tx", "gk", "ck", "tbm")
        tree = ttk.Treeview(top, columns=cols, show="headings")
        tree.heading("mon", text="MÔN"); tree.column("mon", width=110, anchor="w")
        tree.heading("tx", text="TX"); tree.column("tx", width=80, anchor="center")
        tree.heading("gk", text="GK"); tree.column("gk", width=40, anchor="center")
        tree.heading("ck", text="CK"); tree.column("ck", width=40, anchor="center")
        tree.heading("tbm", text="TBM"); tree.column("tbm", width=50, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True, padx=5)
        for ky in ["Kỳ 1", "Kỳ 2"]:
            tree.insert("", tk.END, values=(f"--- {ky.upper()} ---", "", "", "", ""), tags=('header',))
            for mon, p in data.items():
                m = p[ky]
                tx_val = ",".join(map(str, m["TX"])) if m["loai"] == "score" else "--"
                gk_val = m["GK"] if m["loai"] == "score" else "--"
                ck_val = m["CK"] if m["loai"] == "score" else "--"
                tbm_val = tinh_tb_mon(m)
                tree.insert("", tk.END, values=(mon, tx_val, gk_val, ck_val, tbm_val))
        tree.tag_configure('header', background='#dfe6e9', font=("Arial", 10, "bold"))
        tk.Button(top, text="QUAY LẠI", bg="#34495e", fg="white", font=("Arial", 12, "bold"), height=2, command=top.destroy).pack(fill=tk.X, padx=10, pady=10)

    def edit_panel(self):
        edit_win = tk.Toplevel(self.root)
        edit_win.attributes('-fullscreen', True)
        tk.Label(edit_win, text="CHỈNH SỬA ĐIỂM", font=("Arial", 16, "bold"), bg="#e67e22", fg="white", pady=15).pack(fill=tk.X)
        main_f = tk.Frame(edit_win, padx=20, pady=10)
        main_f.pack(fill=tk.BOTH, expand=True)
        ky_var = tk.StringVar(value="Kỳ 1"); mon_var = tk.StringVar(value="Toán học"); status_var = tk.StringVar(value="đạt")
        tk.Label(main_f, text="Học kỳ:").pack(anchor="w")
        ttk.Combobox(main_f, textvariable=ky_var, values=["Kỳ 1", "Kỳ 2"], state="readonly").pack(fill=tk.X, pady=5)
        tk.Label(main_f, text="Môn học:").pack(anchor="w")
        ttk.Combobox(main_f, textvariable=mon_var, values=list(mon_hoc.keys()), state="readonly").pack(fill=tk.X, pady=5)
        score_f = tk.LabelFrame(main_f, text=" Cho môn tính điểm ", padx=10, pady=10); score_f.pack(fill=tk.X, pady=10)
        tk.Label(score_f, text="TX (khoảng trắng):").pack(anchor="w")
        e_tx = tk.Entry(score_f, font=("Arial", 12)); e_tx.pack(fill=tk.X, pady=2)
        tk.Label(score_f, text="GK:").pack(anchor="w"); e_gk = tk.Entry(score_f, font=("Arial", 12)); e_gk.pack(fill=tk.X, pady=2)
        tk.Label(score_f, text="CK:").pack(anchor="w"); e_ck = tk.Entry(score_f, font=("Arial", 12)); e_ck.pack(fill=tk.X, pady=2)
        check_f = tk.LabelFrame(main_f, text=" Cho môn nhận xét ", padx=10, pady=10); check_f.pack(fill=tk.X, pady=10)
        tk.Label(check_f, text="Trạng thái:").pack(side=tk.LEFT)
        ttk.Combobox(check_f, textvariable=status_var, values=["đạt", "chưa đạt"], state="readonly").pack(side=tk.LEFT, padx=10)
        def save_action():
            try:
                m = data[mon_var.get()][ky_var.get()]
                if m["loai"] == "score":
                    m["TX"] = [float(x) for x in e_tx.get().split()] if e_tx.get() else m["TX"]
                    m["GK"] = float(e_gk.get()) if e_gk.get() else m["GK"]
                    m["CK"] = float(e_ck.get()) if e_ck.get() else m["CK"]
                else: m["status"] = status_var.get()
                messagebox.showinfo("Xong", f"Đã lưu môn {mon_var.get()}!")
            except: messagebox.showerror("Lỗi", "Sai định dạng số!")
        tk.Button(main_f, text="LƯU DỮ LIỆU", bg="#27ae60", fg="white", font=("Arial", 13, "bold"), height=2, command=save_action).pack(fill=tk.X, pady=10)
        tk.Button(main_f, text="THOÁT", bg="#bdc3c7", font=("Arial", 11), height=2, command=edit_win.destroy).pack(fill=tk.X, pady=5)

    def terminal_mode(self):
        term = tk.Toplevel(self.root); term.geometry("650x1300"); term.configure(bg="black")
        out = tk.Text(term, bg="black", fg="white", font=("Courier", 10), bd=0); out.pack(fill=tk.BOTH, expand=True)
        info = "--- VN-EDU TERMINAL ---\nLệnh: edit, lock, unlock, home, cls, ex\n> "
        out.insert(tk.END, info); out.config(state=tk.DISABLED)
        inp = tk.Entry(term, bg="black", fg="white", insertbackground="white", font=("Courier", 12)); inp.pack(fill=tk.X, padx=10, pady=10); inp.focus_set()
        
        self.step = 0; self.tmp = {}
        def run(e=None):
            global system_locked
            raw = inp.get().strip(); c = raw.lower(); inp.delete(0, tk.END)
            out.config(state=tk.NORMAL); out.insert(tk.END, f"{raw}\n")
            
            if c == "home":
                self.step = 0; out.insert(tk.END, "\n[SYSTEM RESET]\n> ")
                out.see(tk.END); out.config(state=tk.DISABLED); return

            if self.step == 0:
                if c == "edit":
                    m_txt = "\n[ ALIAS ] t, v, anh, kh, tin, gdtc, sd, cd, cn, n, h\nNhap ma mon: "
                    out.insert(tk.END, m_txt); self.step = 1
                elif c == "lock": system_locked = True; out.insert(tk.END, "[LOCKED]\n> ")
                elif c == "unlock": system_locked = False; out.insert(tk.END, "[UNLOCKED]\n> ")
                elif c == "cls": out.delete('1.0', tk.END); out.insert(tk.END, info)
                elif c == "ex": term.destroy(); return
            elif self.step == 1:
                if c in alias_mon: self.tmp['m'] = alias_mon[c]; out.insert(tk.END, "Ky (1/2): "); self.step = 2
            elif self.step == 2:
                if c in ["1", "2"]:
                    self.tmp['k'] = f"Kỳ {c}"
                    if mon_hoc[self.tmp['m']] == "score": out.insert(tk.END, "TX: "); self.step = 3
                    else: out.insert(tk.END, "KQ (dat/chua): "); self.step = 6
            elif self.step == 3:
                self.tmp['tx'] = [float(x) for x in c.split()] if c else [0.0]; out.insert(tk.END, "GK: "); self.step = 4
            elif self.step == 4:
                self.tmp['gk'] = float(c); out.insert(tk.END, "CK: "); self.step = 5
            elif self.step == 5:
                self.tmp['ck'] = float(c)
                m = data[self.tmp['m']][self.tmp['k']]
                m["TX"], m["GK"], m["CK"] = self.tmp['tx'], self.tmp['gk'], self.tmp['ck']
                out.insert(tk.END, f"[OK] Da luu {self.tmp['m']}\n> "); self.step = 0
            elif self.step == 6:
                data[self.tmp['m']][self.tmp['k']]["status"] = "đạt" if "dat" in c else "chưa đạt"
                out.insert(tk.END, f"[OK] Luu {self.tmp['m']}\n> "); self.step = 0
            out.see(tk.END); out.config(state=tk.DISABLED)
        inp.bind('<Return>', run)

if __name__ == "__main__":
    root = tk.Tk(); app = VnEduMobileUI(root); root.mainloop()
