import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import re
import os
import json
import glob
import random

class ConfigManager:
    def __init__(self, filename="config.json"):
        self.filename = filename
        self.defaults = {
            "font_size_base": 12,
            "font_size_title": 16,
            "btn_scale": 1.0,
            "auto_submit": True, 
            "confirm_exit": True,
            #"default_repo": "",
            "select_all_on_change": False,
            "last_repo": "",       # <-- 新增：记录上次题库
            "last_files": []       # <-- 新增：记录上次选中的文件名列表
        }
        self.config = self.defaults.copy()
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
            except:
                pass

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key):
        return self.config.get(key, self.defaults.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()

class Question:
    def __init__(self, q_type, content, options, correct_answer, raw_text, source_file):
        self.q_type = q_type
        self.content = content
        self.options = options
        self.correct_answer = correct_answer
        self.raw_text = raw_text
        self.source_file = source_file

    def get_id(self):
        clean_content = re.sub(r'\W', '', self.content)
        return clean_content[:50]

class QuestionParser:
    @staticmethod
    def parse_target_files(file_list):
        questions = []
        for filepath in file_list:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    questions.extend(QuestionParser.parse_text(f.read(), os.path.basename(filepath)))
        return questions

    @staticmethod
    def parse_text(text, filename="unknown"):
        parsed_questions = []
        pattern_header = re.compile(r'^\s*(\d+)[\.\、]\s*', re.MULTILINE)
        matches = list(pattern_header.finditer(text))
        
        for i in range(len(matches)):
            start_idx = matches[i].start()
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
            q = QuestionParser.parse_single_block(text[start_idx:end_idx], filename)
            if q: parsed_questions.append(q)
        return parsed_questions

    @staticmethod
    def parse_single_block(block, filename):
        try:
            header_scope = block[:150] 
            
            q_type = 'single'
            if '多选' in header_scope or '[multi]' in header_scope: q_type = 'multi'
            elif '判断' in header_scope or '[judge]' in header_scope: q_type = 'judge'
            elif '填空' in header_scope or '[fill]' in header_scope: q_type = 'fill'
            
            lines = block.split('\n')
            full_content = ""
            
            if len(lines) > 0:
                header = lines[0]
                header = re.sub(r'^\s*\d+[\.\、]\s*', '', header)
                metadata_pattern = r'[\(\[\uff08]\s*(?:单选题|多选题|判断题|填空题|single|multi|judge|fill|.*?分).*?[\)\]\uff09]'
                header = re.sub(metadata_pattern, '', header)
                
                full_content = header.strip()
                if len(lines) > 1:
                    body = "\n".join(lines[1:])
                    full_content += "\n" + body

            stop_patterns = [
                r'(?:^|\n)\s*A[\.\、\s]', 
                r'(?:^|\n)\s*我的答案', 
                r'(?:^|\n)\s*正确答案', 
                r'(?:^|\n)\s*知识点', 
                r'(?:^|\n)\s*AI讲解',
                r'\[single\]', r'\[multi\]',
                r'(?:^|\n)\s*\d+分[一二三四]', 
                r'(?:^|\n)\s*一\.\s*单选题',
                r'(?:^|\n)\s*二\.\s*多选题'
            ]
            
            min_split_index = len(full_content)
            for pat in stop_patterns:
                m = re.search(pat, full_content, re.IGNORECASE)
                if m: min_split_index = min(min_split_index, m.start())
            
            q_content = full_content[:min_split_index].strip() or "(题目解析内容为空)"

            options = []
            if q_type in ['single', 'multi']:
                opt_iter = re.finditer(r'(?:^|\n)\s*([A-Z])[\.\、]\s*(.*?)(?=\n\s*[A-Z][\.\、]|\n\s*我的答案|\n\s*正确答案|$)', block, re.DOTALL)
                for m in opt_iter: 
                    options.append(f"{m.group(1)}. {m.group(2).strip()}")
            elif q_type == 'judge':
                options = ["A. 对", "B. 错"]

            correct_ans = ""
            ans_match = re.search(r'正确答案[:：](.*?)(?:;|\n|知识点|AI|$)', block)
            if ans_match:
                raw_ans = ans_match.group(1).strip()
                if q_type == 'judge':
                    if '对' in raw_ans or 'T' in raw_ans: correct_ans = 'A'
                    elif '错' in raw_ans or 'F' in raw_ans: correct_ans = 'B'
                    else: correct_ans = raw_ans
                elif q_type == 'fill':
                    correct_ans = raw_ans
                else:
                    correct_ans = "".join(re.findall(r'[A-Z]', raw_ans))
            
            if not correct_ans and q_type == 'fill':
                ans_match_2 = re.search(r'正确答案[:：]\s*\n(.*?)(?:\n知识点|\nAI|$)', block, re.DOTALL)
                if ans_match_2: correct_ans = ans_match_2.group(1).strip()

            return Question(q_type, q_content, options, correct_ans, block, filename)
        except: 
            return None

class MistakeManager:
    def __init__(self, filename="mistakes.json"):
        self.filename = filename
        self.data = {}
        self.load()
    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f: self.data = json.load(f)
            except: self.data = {}
    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f: json.dump(self.data, f, ensure_ascii=False, indent=2)
    def add_mistake(self, q_id):
        self.data[q_id] = self.data.get(q_id, 0) + 1
        self.save()
    def get_count(self, q_id): return self.data.get(q_id, 0)
    def get_max_errors(self): return max(self.data.values()) if self.data else 0

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 刷题")

        if os.path.exists("favicon.ico"):
            try:
                self.root.iconbitmap("favicon.ico")
            except:
                pass

        self.root.geometry("1000x800")
        
        self.cfg = ConfigManager()
        self.mistake_mgr = MistakeManager()
        self.txt_files = glob.glob("*.txt")
        self.all_questions_cache = QuestionParser.parse_target_files(self.txt_files)
        
        self.session_stats = {'total': 0, 'correct': 0}
        self.current_queue = []
        self.current_index = 0
        self.current_q = None
        
        self.type_map = {'single': '单选题', 'multi': '多选题', 'judge': '判断题', 'fill': '填空题'}
        
        self.filter_vars = {
            'single': tk.BooleanVar(value=True),
            'multi':  tk.BooleanVar(value=True),
            'judge':  tk.BooleanVar(value=True),
            'fill':   tk.BooleanVar(value=True)
        }
        
        self.setup_menu()

    def get_fonts(self):
        base = self.cfg.get("font_size_base")
        title = self.cfg.get("font_size_title")
        return {
            "title": ("微软雅黑", title, "bold"),
            "normal": ("微软雅黑", base),
            "ui": ("微软雅黑", base - 2),
            "btn": ("微软雅黑", base)
        }

    def open_settings(self):
        """打开设置窗口"""
        win = tk.Toplevel(self.root)
        win.title("界面设置")
        win.geometry("400x550") 
        win.grab_set() 
        
        fonts = self.get_fonts()
        
        tk.Label(win, text="题目字体大小:", font=fonts["normal"]).pack(pady=10)
        scale_font = tk.Scale(win, from_=10, to=30, orient=tk.HORIZONTAL, length=200)
        scale_font.set(self.cfg.get("font_size_title"))
        scale_font.pack()
        
        tk.Label(win, text="选项/按钮字体大小:", font=fonts["normal"]).pack(pady=10)
        scale_base = tk.Scale(win, from_=8, to=24, orient=tk.HORIZONTAL, length=200)
        scale_base.set(self.cfg.get("font_size_base"))
        scale_base.pack()
        
        ttk.Separator(win, orient='horizontal').pack(fill='x', pady=20)

        # tk.Label(win, text="默认启动题库:", font=fonts["normal"]).pack(pady=5)
        
        # base_dir = "题库"
        # if not os.path.exists(base_dir): os.makedirs(base_dir)
        # repos = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        
        # combo_def_repo = ttk.Combobox(win, values=repos, state="readonly", font=fonts["normal"], width=20)
        # combo_def_repo.pack(pady=5)
        
        # curr_repo = self.cfg.get("default_repo")
        # if curr_repo and curr_repo in repos:
            # combo_def_repo.set(curr_repo)
        # elif repos:
            # combo_def_repo.current(0)
        # else:
            # combo_def_repo.set("无题库")

        # ttk.Separator(win, orient='horizontal').pack(fill='x', pady=20)

        var_auto = tk.BooleanVar(value=self.cfg.get("auto_submit"))
        chk_auto = tk.Checkbutton(win, text="单选/判断题点击选项直接判分", variable=var_auto, font=fonts["normal"])
        chk_auto.pack(pady=5, anchor="w", padx=50)

        current_confirm = self.cfg.get("confirm_exit")
        if current_confirm is None: current_confirm = True
        var_exit = tk.BooleanVar(value=current_confirm)
        chk_exit = tk.Checkbutton(win, text="返回主页时显示确认提示", variable=var_exit, font=fonts["normal"])
        chk_exit.pack(pady=5, anchor="w", padx=50)


        var_sel_all = tk.BooleanVar(value=self.cfg.get("select_all_on_change"))
        chk_sel_all = tk.Checkbutton(win, text="切换/加载题库时默认全选文件", variable=var_sel_all, font=fonts["normal"])
        chk_sel_all.pack(pady=5, anchor="w", padx=50)

        def save_conf():
            self.cfg.set("font_size_title", scale_font.get())
            self.cfg.set("font_size_base", scale_base.get())
            self.cfg.set("auto_submit", var_auto.get())
            self.cfg.set("confirm_exit", var_exit.get())

            # 保存全选配置
            self.cfg.set("select_all_on_change", var_sel_all.get())
            
            # new_repo = combo_def_repo.get()
            # if new_repo and new_repo != "无题库":
            #     self.cfg.set("default_repo", new_repo)
            
            messagebox.showinfo("提示", "设置已保存！")
            win.destroy()
            
            if not self.current_q:
                self.setup_menu()

        tk.Button(win, text="保存并关闭", command=save_conf, bg="#4caf50", fg="white", font=fonts["btn"]).pack(pady=20)

    def setup_menu(self):
        self.clear_window()
        fonts = self.get_fonts()
        self.current_q = None 
        
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")
        
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill="x", pady=10)
        tk.Label(header_frame, text="Python 刷题", font=("微软雅黑", 22, "bold")).pack(side="left")
        tk.Button(header_frame, text="⚙ 设置", command=self.open_settings, font=fonts["ui"]).pack(side="right")
        
        repo_frame = tk.LabelFrame(main_frame, text="0. 切换题库", font=fonts["normal"], padx=10, pady=10)
        repo_frame.pack(fill="x", pady=5)
        
        base_dir = "题库"
        if not os.path.exists(base_dir): os.makedirs(base_dir)
        repos = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        
        if not repos:
            tk.Label(repo_frame, text="未在“题库”文件夹下发现子文件夹！", fg="red", font=fonts["normal"]).pack()
            self.combo_repo = None
        else:
            tk.Label(repo_frame, text="当前题库:", font=fonts["normal"]).pack(side="left")
            self.combo_repo = ttk.Combobox(repo_frame, values=repos, state="readonly", font=fonts["normal"], width=20)
            self.combo_repo.pack(side="left", padx=10)
            
            # === 修改：加载上次记忆的题库 ===
            last_repo = self.cfg.get("last_repo")
            if last_repo and last_repo in repos:
                self.combo_repo.set(last_repo)
            else:
                self.combo_repo.current(0)
                
            self.combo_repo.bind("<<ComboboxSelected>>", self.refresh_file_list)

        file_frame = tk.LabelFrame(main_frame, text="1. 选择题目文件 (Ctrl+点击多选)", font=fonts["normal"], padx=10, pady=10)
        file_frame.pack(fill="x", pady=10, expand=True)


        mistake_ctrl_frame = tk.Frame(file_frame)
        mistake_ctrl_frame.pack(fill="x", pady=(0, 5))
        
        self.var_mistake_mode = tk.BooleanVar(value=False)
        chk_mistake = tk.Checkbutton(mistake_ctrl_frame, text="采用错题模式: 错", variable=self.var_mistake_mode, font=fonts["normal"], fg="#d32f2f")
        chk_mistake.pack(side="left")
        
        self.combo_mistake = ttk.Combobox(mistake_ctrl_frame, width=5, state="readonly", font=fonts["normal"])
        self.combo_mistake.pack(side="left", padx=5)
        
        tk.Label(mistake_ctrl_frame, text="次的题", font=fonts["normal"]).pack(side="left")

        list_scroll = tk.Scrollbar(file_frame)
        list_scroll.pack(side="right", fill="y")
        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.MULTIPLE, height=6, 
                                       font=("Consolas", self.cfg.get("font_size_base")), yscrollcommand=list_scroll.set)
        self.file_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.config(command=self.file_listbox.yview)
        
        
        filter_frame = tk.LabelFrame(main_frame, text="2. 题型过滤", font=fonts["normal"], padx=10, pady=10)
        filter_frame.pack(fill="x", pady=10)
        
        type_display = [('单选题', 'single'), ('多选题', 'multi'), ('判断题', 'judge'), ('填空题', 'fill')]
        for txt, key in type_display:
            tk.Checkbutton(filter_frame, text=txt, variable=self.filter_vars[key], font=fonts["normal"]).pack(side="left", padx=15)

        action_frame = tk.LabelFrame(main_frame, text="3. 开始练习", font=fonts["normal"], padx=10, pady=10)
        action_frame.pack(fill="x", pady=10)

        btn_w = 15
        tk.Button(action_frame, text="顺序练习", width=btn_w, height=2, font=fonts["btn"], bg="#e3f2fd",
                  command=lambda: self.start_selected_practice(shuffle=False)).pack(side="left", padx=20)
        tk.Button(action_frame, text="随机练习", width=btn_w, height=2, font=fonts["btn"], bg="#e3f2fd",
                  command=lambda: self.start_selected_practice(shuffle=True)).pack(side="left", padx=20)
        
        # tk.Frame(main_frame, height=2, bg="#ddd").pack(fill="x", pady=15)
        # mistake_frame = tk.Frame(main_frame)
        # mistake_frame.pack(pady=5)
        
        # tk.Label(mistake_frame, text="错题复习: 错", font=fonts["normal"]).pack(side="left")
        # max_err = self.mistake_mgr.get_max_errors()
        # vals = list(range(1, max_err + 1)) if max_err > 0 else ["无"]
        # self.combo_mistake = ttk.Combobox(mistake_frame, values=vals, width=5, state="readonly", font=fonts["normal"])
        # if max_err > 0: self.combo_mistake.current(0)
        # else: self.combo_mistake.set("无")
        # self.combo_mistake.pack(side="left", padx=5)
        # tk.Label(mistake_frame, text="次的题", font=fonts["normal"]).pack(side="left")
        # tk.Button(mistake_frame, text="Go", font=fonts["btn"], bg="#ffe0b2", command=self.start_mistake_review).pack(side="left", padx=15)

        if getattr(self, 'combo_repo', None):
            self.refresh_file_list()


    def refresh_file_list(self, event=None):
        if not getattr(self, 'combo_repo', None): return
        if not self.combo_repo.winfo_exists(): return

        current_repo = self.combo_repo.get()
        self.file_listbox.delete(0, tk.END)
        
        search_path = os.path.join("题库", current_repo, "*.txt")
        self.current_txt_paths = glob.glob(search_path) 
        
        # 用于映射：文件名 -> Listbox索引
        name_to_index = {}

        if not self.current_txt_paths:
            self.file_listbox.insert(tk.END, "(该文件夹下无txt文件)")
            self.all_questions_cache = []
        else:
            for idx, p in enumerate(self.current_txt_paths):
                fname = os.path.basename(p)
                self.file_listbox.insert(tk.END, fname)
                name_to_index[fname] = idx
            
            self.all_questions_cache = QuestionParser.parse_target_files(self.current_txt_paths)

            last_repo = self.cfg.get("last_repo")
            last_files = self.cfg.get("last_files") or []

            # 只有当当前下拉框显示的题库 == 配置文件里记录的上次题库时，才尝试恢复
            if current_repo == last_repo:
                missing_files = []
                has_selection = False
                
                for f_name in last_files:
                    if f_name in name_to_index:
                        self.file_listbox.select_set(name_to_index[f_name])
                        has_selection = True
                    else:
                        # 如果上次记录的文件不在当前列表里，说明文件丢失了
                        missing_files.append(f_name)
                
                # 如果有丢失的文件，弹出警告
                if missing_files:
                    msg = "以下上次选中的文件未找到（可能已被删除或重命名）：\n\n" + "\n".join(missing_files)
                    messagebox.showwarning("文件丢失提示", msg)
            
            # 如果不是上次的题库，或者上次没选文件，则检查是否配置了“默认全选”
            elif self.cfg.get("select_all_on_change"):
                self.file_listbox.select_set(0, tk.END)
            # ========================

            local_max_err = 0
            if self.all_questions_cache:
                for q in self.all_questions_cache:
                    cnt = self.mistake_mgr.get_count(q.get_id())
                    if cnt > local_max_err: local_max_err = cnt
            
            if getattr(self, 'combo_mistake', None) and self.combo_mistake.winfo_exists():
                vals = ["所有"] + list(range(1, local_max_err + 1)) if local_max_err > 0 else ["无"]
                self.combo_mistake['values'] = vals
                
                # 如果之前没选值，或者当前值不在新列表里，重置为第一个
                if self.combo_mistake.get() not in [str(v) for v in vals]:
                    if local_max_err > 0: self.combo_mistake.current(0) # 默认选 "所有"
                    else: self.combo_mistake.set("无")



        # 错题库联动逻辑
        local_max_err = 0
        if self.all_questions_cache:
            for q in self.all_questions_cache:
                cnt = self.mistake_mgr.get_count(q.get_id())
                if cnt > local_max_err: local_max_err = cnt
        
        if getattr(self, 'combo_mistake', None) and self.combo_mistake.winfo_exists():
            vals = ["所有"] + list(range(1, local_max_err + 1)) if local_max_err > 0 else ["无"]
            self.combo_mistake['values'] = vals
            if local_max_err > 0: self.combo_mistake.current(0)
            else: self.combo_mistake.set("无")


    def get_allowed_types(self):
        return [k for k, v in self.filter_vars.items() if v.get()]

    def start_selected_practice(self, shuffle):
        idxs = self.file_listbox.curselection()
        if not idxs: return messagebox.showwarning("提示", "请先勾选至少一个题库文件！")
        
        selected_filenames = [self.file_listbox.get(i) for i in idxs]
        
        if "(该文件夹下无txt文件)" in selected_filenames:
            return
        
        # 保存配置
        if getattr(self, 'combo_repo', None):
            repo_dir = self.combo_repo.get()
            self.cfg.set("last_repo", repo_dir)
            self.cfg.set("last_files", selected_filenames)
            # 重新构建完整路径用于解析（如果你没有缓存机制，就用这个；如果有all_questions_cache，就用下面的过滤）
            files = [os.path.join("题库", repo_dir, fname) for fname in selected_filenames]
        
        qs = QuestionParser.parse_target_files(files) 
        
        allowed = self.get_allowed_types()
        qs = [q for q in qs if q.q_type in allowed]
        
        if self.var_mistake_mode.get():
            target_err = self.combo_mistake.get() # 获取下拉框的值 (如 "所有", "1", "2"...)
            if not target_err or target_err == "无":
                return messagebox.showinfo("提示", "当前没有错题记录，无法开启错题模式。")
            
            filtered_qs = []
            for q in qs:
                err_count = self.mistake_mgr.get_count(q.get_id())
                if target_err == "所有":
                    if err_count > 0: filtered_qs.append(q)
                else:
                    try:
                        if err_count == int(target_err): filtered_qs.append(q)
                    except: pass
            
            qs = filtered_qs # 用过滤后的错题列表覆盖原列表
            
            if not qs:
                return messagebox.showinfo("提示", f"在所选文件中，没有找到符合“错误{target_err}次”的题目。")
        
        if not qs: return messagebox.showerror("错误", "所选条件（文件/题型/错题）下没有题目！")
        self.start_quiz(qs, shuffle)

    def start_mistake_review(self):
        val = self.combo_mistake.get()
        if val in ["无", ""]: return
        
        # 1. 获取列表框中选中的文件名
        idxs = self.file_listbox.curselection()
        if not idxs:
            messagebox.showwarning("提示", "请先在左侧列表中勾选要复习的题目文件！")
            return
        
        selected_files = set(self.file_listbox.get(i) for i in idxs)
        allowed = self.get_allowed_types()
        
        qs = []
        
        if val == "所有":
            # 筛选逻辑：属于选中文件 + 错误次数大于0 + 题型匹配
            qs = [
                q for q in self.all_questions_cache 
                if q.source_file in selected_files 
                and self.mistake_mgr.get_count(q.get_id()) > 0 
                and q.q_type in allowed
            ]
        else:
            # 筛选逻辑：属于选中文件 + 错误次数等于特定值 + 题型匹配
            try:
                target_count = int(val)
                qs = [
                    q for q in self.all_questions_cache 
                    if q.source_file in selected_files 
                    and self.mistake_mgr.get_count(q.get_id()) == target_count 
                    and q.q_type in allowed
                ]
            except ValueError:
                return # 防止解析错误

        if not qs: 
            messagebox.showinfo("提示", "在所选文件和题型中，没有找到符合条件的错题。")
            return
            
        self.start_quiz(qs, shuffle=True)

    def start_quiz(self, questions, shuffle):
        self.current_queue = list(questions)
        if shuffle: random.shuffle(self.current_queue)
        self.current_index = 0
        self.session_stats = {'total': 0, 'correct': 0}
        self.show_question_ui()

    def clear_window(self):
        for widget in self.root.winfo_children(): widget.destroy()

    def return_to_menu(self): 
        need_confirm = self.cfg.get("confirm_exit")
        if need_confirm is None: need_confirm = True

        if need_confirm:
            if not messagebox.askyesno("退出", "确定要退出练习吗？\n目前的进度将丢失。"):
                return 

        self.setup_menu()

    def show_summary(self):
        total = self.session_stats['total']
        correct = self.session_stats['correct']
        acc = (correct / total * 100) if total > 0 else 0.0
        msg = f"练习完成！\n\n共答: {total} 题\n正确: {correct} 题\n正确率: {acc:.2f}%"
        messagebox.showinfo("结果结算", msg)
        self.setup_menu()

    def ask_jump_question(self):
        max_q = len(self.current_queue)
        target = simpledialog.askinteger("跳转", f"请输入题号 (1-{max_q}):", 
                                       minvalue=1, maxvalue=max_q, parent=self.root)
        if target:
            self.current_index = target - 1
            self.show_question_ui()

    def show_question_ui(self):
        self.clear_window()
        if self.current_index >= len(self.current_queue):
            self.show_summary()
            return

        q = self.current_q = self.current_queue[self.current_index]
        fonts = self.get_fonts()
        
        # --- 顶部导航栏 ---
        top_bar = tk.Frame(self.root, bg="#eee", pady=8, padx=10)
        top_bar.pack(fill="x", side="top")
        
        tk.Button(top_bar, text="< 主页", command=self.return_to_menu, font=fonts["ui"], bg="#ddd").pack(side="left")
        
        center_info = f"进度: {self.current_index + 1} / {len(self.current_queue)}"
        tk.Label(top_bar, text=center_info, bg="#eee", font=("微软雅黑", fonts["ui"][1], "bold")).pack(side="left", padx=20)
        
        right_frame = tk.Frame(top_bar, bg="#eee")
        right_frame.pack(side="right")

        err_count = self.mistake_mgr.get_count(q.get_id())
        err_color = "#d32f2f" if err_count > 0 else "#999"
        tk.Label(right_frame, text=f"错误: {err_count}", bg="#eee", font=fonts["ui"], fg=err_color).pack(side="left", padx=10)
        
        tk.Label(right_frame, text=f"来源: {q.source_file}", bg="#eee", font=fonts["ui"], fg="#666").pack(side="left", padx=10)
        tk.Button(right_frame, text="↷ 跳转", command=self.ask_jump_question, font=fonts["ui"], bg="#b2dfdb").pack(side="left")

        bottom_frame = tk.Frame(self.root, pady=20, bg="#f0f0f0")
        bottom_frame.pack(side="bottom", fill="x")

        self.feedback_label = tk.Label(bottom_frame, text="", font=("微软雅黑", fonts["normal"][1], "bold"), bg="#f0f0f0")
        self.feedback_label.pack(pady=(0, 10))

        btn_container = tk.Frame(bottom_frame, bg="#f0f0f0")
        btn_container.pack(anchor="center") 

        self.btn_submit = tk.Button(btn_container, text="提交答案", command=self.check_answer, 
                                    bg="#4caf50", fg="white", font=fonts["btn"], width=20, height=2)
        self.btn_submit.pack(side="top", pady=(0, 15)) # pady 保证和下方按钮有间距

        nav_frame = tk.Frame(btn_container, bg="#f0f0f0")
        nav_frame.pack(side="top")

        self.btn_prev = tk.Button(nav_frame, text="<< 上一题", command=self.prev_question, 
                                  font=fonts["btn"], width=15, height=2, bg="#e0e0e0")
        self.btn_prev.pack(side="left", padx=10) # padx 保证两个按钮中间有空隙
        
        self.btn_next = tk.Button(nav_frame, text="下一题 >>", command=self.next_question, 
                                  state="normal", font=fonts["btn"], width=15, height=2, bg="#2196f3", fg="white")
        self.btn_next.pack(side="left", padx=10)

        if self.current_index == 0:
            self.btn_prev.config(state="disabled")

        canvas = tk.Canvas(self.root, bg="white")
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg="white")

        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        def on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_resize)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content_box = tk.Frame(self.scroll_frame, bg="white", padx=40, pady=30)
        content_box.pack(fill="x", expand=True)

        type_cn = self.type_map.get(q.q_type, q.q_type)
        full_text = f"[{type_cn}] {q.content}"
        
        self.lbl_question = tk.Label(content_box, text=full_text, font=fonts["title"], bg="white",
                                     justify="left", anchor="w")
        self.lbl_question.pack(fill="x", pady=(0, 20))
        
        def update_wrap(event):
            self.lbl_question.config(wraplength=event.width - 10)
        
        self.lbl_question.bind("<Configure>", update_wrap)

        opts_frame = tk.Frame(content_box, bg="white")
        opts_frame.pack(fill="x", anchor="w")
        
        self.input_vars = [] 
        
        def auto_submit_if_enabled():
            if self.cfg.get("auto_submit") and self.btn_submit['state'] != 'disabled':
                self.check_answer()

        if q.q_type in ['single', 'judge']:
            self.var_single = tk.StringVar(value="UNSELECTED_SAFE")
            for opt in q.options:
                rb = tk.Radiobutton(opts_frame, text=opt, variable=self.var_single, value=opt[0], 
                                    font=fonts["normal"], justify="left", bg="white",
                                    tristatevalue="TRISTATE_SAFE",
                                    command=auto_submit_if_enabled)
                rb.pack(anchor="w", pady=8, fill="x")
                rb.bind("<Configure>", lambda e, r=rb: r.config(wraplength=e.width - 10))
                
        elif q.q_type == 'multi':
            for opt in q.options:
                var = tk.IntVar(value=0)
                cb = tk.Checkbutton(opts_frame, text=opt, variable=var, onvalue=1, offvalue=0, 
                                    font=fonts["normal"], justify="left", bg="white")
                cb.pack(anchor="w", pady=8, fill="x")
                cb.bind("<Configure>", lambda e, c=cb: c.config(wraplength=e.width - 10))
                self.input_vars.append((opt[0], var))
                
        elif q.q_type == 'fill':
            tk.Label(opts_frame, text="思考后输入答案：", font=fonts["normal"], bg="white").pack(anchor="w")
            self.entry_fill = tk.Text(opts_frame, height=4, font=fonts["normal"])
            self.entry_fill.pack(anchor="w", pady=5, fill="x")

    def check_answer(self):
        q = self.current_q
        user_ans = ""
        is_correct = False
        
        if q.q_type in ['single', 'judge']:
            user_ans = self.var_single.get()
            if user_ans == "UNSELECTED_SAFE":
                messagebox.showwarning("提示", "请选择一个选项！")
                return
            is_correct = (user_ans == q.correct_answer)
        elif q.q_type == 'multi':
            selected = [code for code, var in self.input_vars if var.get() == 1]
            if not selected:
                messagebox.showwarning("提示", "请至少选择一个选项！")
                return
            user_ans = "".join(sorted(selected))
            correct_sorted = "".join(sorted(list(q.correct_answer)))
            is_correct = (user_ans == correct_sorted)
        elif q.q_type == 'fill':
            user_text = self.entry_fill.get("1.0", "end").strip()
            is_correct = (user_text == q.correct_answer)

        self.session_stats['total'] += 1
        if is_correct:
            self.session_stats['correct'] += 1
            self.feedback_label.config(text="回答正确！✅", fg="green")
            self.btn_submit.config(state="disabled")
            
            self.root.after(600, self.next_question) 
        else:
            self.mistake_mgr.add_mistake(q.get_id())
            ans_show = q.correct_answer
            if q.q_type == 'judge': ans_show = "正确" if q.correct_answer == 'A' else "错误"
            msg = f"回答错误 ❌\n正确答案: {ans_show}"
            self.feedback_label.config(text=msg, fg="red")
            self.btn_submit.config(state="disabled")

    def next_question(self):
        self.current_index += 1
        self.show_question_ui()

    def prev_question(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question_ui()

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    app = QuizApp(root)
    root.mainloop()
