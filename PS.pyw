# Copyright (c) 2026 Iviesever

# The MIT License (MIT)
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# github: https://github.com/Iviesever/Python-practice-questions

import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import tkinter.font as tkfont
import re
import os
import json
import glob
import random
import time
from datetime import datetime

class ConfigManager:
    def __init__(self, filename="config.json"):
        self.filename = filename
        self.defaults = {
            "font_size_base": 12,
            "font_size_title": 16,
            "btn_scale": 1.0,
            "auto_submit": True, 
            "confirm_exit": True,
            "file_selection_mode": "remembered", # 可选值: "all" (全选) 或 "remembered" (记忆)
            "last_repo": "",       # 记录上次题库
            "last_files": [],       # 记录上次选中的文件名列表
            "mistake_operator": "不启用", # 默认不启用
            "mistake_value": "1"          # 默认次数
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
        # 清洗底部统计区
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            if re.search(r'一\.\s*单选题.*?\n\s*1\s+2\s+3', line) or re.match(r'^1\s+2\s+3\s+4', line): break
            if re.match(r'^\s*AI讲解\s*$', line) or re.match(r'^\s*\d+(\.\d+)?分\s*$', line): continue
            clean_lines.append(line)
        text = "\n".join(clean_lines)

        parsed_questions = []
        pattern_header = re.compile(r'^\s*(\d+)[\.\、]\s*', re.MULTILINE)
        matches = list(pattern_header.finditer(text))
        
        for i in range(len(matches)):
            start_idx = matches[i].start()
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
            block = text[start_idx:end_idx]
            q = QuestionParser.parse_single_block(block, filename)
            if q: parsed_questions.append(q)
        return parsed_questions

    @staticmethod
    def parse_single_block(block, filename):
        try:
            q_type = 'single'
            if '多选' in block[:50]: q_type = 'multi'
            elif '判断' in block[:50]: q_type = 'judge'
            elif '填空' in block[:50]: q_type = 'fill'
            
            content = re.sub(r'^\s*\d+[\.\、]\s*', '', block).strip()
            content = re.sub(r'[\(\[\uff08]\s*(?:单选题|多选题|判断题|填空题|.*?分).*?[\)\]\uff09]', '', content)
            
            stop_patterns = [r'(?:^|\n)\s*[A-Z][\.\、]', r'我的答案', r'正确答案', r'AI讲解', r'\d+分', r'\(1\)']
            min_split = len(content)
            for pat in stop_patterns:
                m = re.search(pat, content)
                if m: min_split = min(min_split, m.start())
            q_content = content[:min_split].strip()
            if not q_content: return None

            options = []
            if q_type in ['single', 'multi']:
                opt_iter = re.finditer(r'(?:^|\n)\s*([A-Z])[\.\、]\s*(.*?)(?=\n\s*[A-Z][\.\、]|\n\s*我的答案|\n\s*正确答案|\n\s*\d+分|$)', block, re.DOTALL)
                for m in opt_iter: options.append(f"{m.group(1)}. {m.group(2).strip()}")
            elif q_type == 'judge': options = ["A. 对", "B. 错"]

            ans_match = re.search(r'正确答案[:：]\s*(?:[\r\n]+)?(.*)', block, re.DOTALL)
            correct_ans = ""
            if ans_match:
                raw = ans_match.group(1).strip()
                end_of_ans = len(raw)
                for stop in ['AI讲解', '\n', '1. ']: 
                    idx = raw.find(stop); 
                    if idx != -1: end_of_ans = min(end_of_ans, idx)
                raw_clean = raw[:end_of_ans].strip()
                if q_type == 'judge':
                    if '对' in raw_clean or 'T' in raw_clean: correct_ans = 'A'
                    elif '错' in raw_clean or 'F' in raw_clean: correct_ans = 'B'
                    else: correct_ans = raw_clean
                elif q_type == 'fill': correct_ans = re.sub(r'^\(\d+\)\s*', '', raw_clean)
                else: correct_ans = "".join(re.findall(r'[A-Z]', raw_clean))

            if q_type in ['single', 'multi'] and not options: return None
            return Question(q_type, q_content, options, correct_ans, block, filename)
        except: return None

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


# 新增考试配置和历史记录管理类
class ExamConfigManager:
    """管理考试配置预设 (题目数量、分值、时间)"""
    def __init__(self, filename="exam_presets.json"):
        self.filename = filename
        self.presets = {}
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.presets = json.load(f)
            except: self.presets = {}

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.presets, f, indent=2)

    def get_preset(self, name):
        return self.presets.get(name, None)

    def save_preset(self, name, data):
        self.presets[name] = data
        self.save()
    
    def get_names(self):
        return list(self.presets.keys())

# 管理考试历史记录
class ExamHistoryManager:
    def __init__(self, filename="exam_history.json"):
        self.filename = filename
        self.history = {} # { "repo_name": [record1, record2...] }
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except: self.history = {}

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def add_record(self, repo_name, record):
        if repo_name not in self.history:
            self.history[repo_name] = []
        self.history[repo_name].insert(0, record) # 新的在前
        self.save()

    def get_records(self, repo_name):
        return self.history.get(repo_name, [])


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


        # 初始化管理器 
        self.exam_cfg_mgr = ExamConfigManager()
        self.exam_hist_mgr = ExamHistoryManager()
        self.exam_mode = False # 标记当前是否在模拟考试中
        self.exam_timer_id = None
        self.exam_end_time = 0



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


    def show_settings_page(self):
        """显示设置页面（覆盖主窗口）"""
        self.clear_window() # 清空当前窗口内容
        
        # 定义动态字体对象（仅用于预览）
        f_title_obj = tkfont.Font(family="微软雅黑", size=self.cfg.get("font_size_title"), weight="bold")
        f_base_obj = tkfont.Font(family="微软雅黑", size=self.cfg.get("font_size_base"))
        
        # 顶部返回栏
        top_bar = tk.Frame(self.root, bg="#eee", pady=10)
        top_bar.pack(fill="x", side="top")
        tk.Button(top_bar, text="< 返回", command=self.setup_menu, font=f_base_obj).pack(side="left", padx=10)
        tk.Label(top_bar, text="设置", font=("微软雅黑", 16, "bold"), bg="#eee").pack(side="left", padx=10)

        # 主滚动区域
        canvas = tk.Canvas(self.root)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, padx=20, pady=20)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 字体设置
        def update_title_font(val):
            f_title_obj.configure(size=int(val))
        def update_base_font(val):
            f_base_obj.configure(size=int(val))

        tk.Label(scroll_frame, text="题目字号", font=f_base_obj).pack(pady=10, anchor="w")
        scale_font = tk.Scale(scroll_frame, from_=3, to=30, orient=tk.HORIZONTAL, length=300, 
                              command=update_title_font) 
        scale_font.set(self.cfg.get("font_size_title"))
        scale_font.pack(anchor="w")
        
        tk.Label(scroll_frame, text="字号预览", font=f_title_obj, fg="#1976d2").pack(pady=5, anchor="w")
        
        tk.Label(scroll_frame, text="选项/按钮大小", font=f_base_obj).pack(pady=10, anchor="w")
        scale_base = tk.Scale(scroll_frame, from_=3, to=30, orient=tk.HORIZONTAL, length=300,
                              command=update_base_font)
        scale_base.set(self.cfg.get("font_size_base"))
        scale_base.pack(anchor="w")
        
        ttk.Separator(scroll_frame, orient='horizontal').pack(fill='x', pady=20)

        # 选项设置
        var_auto = tk.BooleanVar(value=self.cfg.get("auto_submit"))
        chk_auto = tk.Checkbutton(scroll_frame, text="单选/判断题点击选项直接判分", variable=var_auto, font=f_base_obj)
        chk_auto.pack(pady=5, anchor="w")

        var_exit = tk.BooleanVar(value=self.cfg.get("confirm_exit") if self.cfg.get("confirm_exit") is not None else True)
        chk_exit = tk.Checkbutton(scroll_frame, text="返回主页时显示确认提示", variable=var_exit, font=f_base_obj)
        chk_exit.pack(pady=5, anchor="w")

        ttk.Separator(scroll_frame, orient='horizontal').pack(fill='x', pady=20)
        
        # 题库加载
        tk.Label(scroll_frame, text="切换/加载题库时的默认行为:", font=f_base_obj).pack(pady=(0, 5), anchor="w")
        current_mode = self.cfg.get("file_selection_mode") 
        if current_mode not in ["all", "remembered"]: current_mode = "remembered"
        
        var_sel_mode = tk.StringVar(value=current_mode)
        tk.Radiobutton(scroll_frame, text="记忆上次选中的文件", variable=var_sel_mode, value="remembered", font=f_base_obj).pack(pady=2, anchor="w")
        tk.Radiobutton(scroll_frame, text="默认全选所有文件", variable=var_sel_mode, value="all", font=f_base_obj).pack(pady=2, anchor="w")

        def save_conf():
            self.cfg.set("font_size_title", scale_font.get())
            self.cfg.set("font_size_base", scale_base.get())
            self.cfg.set("auto_submit", var_auto.get())
            self.cfg.set("confirm_exit", var_exit.get())
            self.cfg.set("file_selection_mode", var_sel_mode.get())
            
            messagebox.showinfo("提示", "设置已保存！")
            self.setup_menu() # 保存后直接返回主页

        # 底部
        tk.Button(scroll_frame, text="保存设置并返回主页", command=save_conf, 
                  bg="#4caf50", fg="white", font=f_base_obj, height=2).pack(pady=30, fill="x")

    # 适配手机屏幕布局 
    def setup_menu(self):
        self.clear_window()
        fonts = self.get_fonts()
        self.current_q = None 
        
        # 主容器
        main_frame = tk.Frame(self.root, padx=10, pady=10) # 减小边距
        main_frame.pack(expand=True, fill="both")
        
        # 顶部标题
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill="x", pady=5)
        
        tk.Label(header_frame, text="Python 刷题", font=("微软雅黑", 18, "bold")).pack(side="left")
        tk.Button(header_frame, text="设置", command=self.show_settings_page, font=fonts["ui"]).pack(side="right")
        
        # 0. 切换题库
        repo_frame = tk.LabelFrame(main_frame, text="0. 切换题库", font=fonts["normal"], padx=5, pady=5)
        repo_frame.pack(fill="x", pady=5)
        
        base_dir = "题库"
        if not os.path.exists(base_dir): os.makedirs(base_dir)
        repos = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        
        if not repos:
            tk.Label(repo_frame, text="未发现题库文件夹！", fg="red", font=fonts["normal"]).pack()
            self.combo_repo = None
        else:
            self.combo_repo = ttk.Combobox(repo_frame, values=repos, state="readonly", font=fonts["normal"])
            self.combo_repo.pack(fill="x", padx=5) # 让下拉框填满宽度
            
            last_repo = self.cfg.get("last_repo")
            if last_repo and last_repo in repos:
                self.combo_repo.set(last_repo)
            else:
                self.combo_repo.current(0)
            self.combo_repo.bind("<<ComboboxSelected>>", self.refresh_file_list)

        # 1. 选择题目文件
        file_frame_title = "1. 选择题目文件"
        file_frame = tk.LabelFrame(main_frame, text=file_frame_title, font=fonts["normal"], padx=5, pady=5)
        file_frame.pack(fill="x", pady=5, expand=True)

        # 工具栏分成上下两行，防止手机上挤在一起
        toolbar_frame = tk.Frame(file_frame)
        toolbar_frame.pack(fill="x", pady=(0, 5))

        # 第一行：全选按钮
        def toggle_select_all():
            if self.file_listbox.size() == 0: return
            if len(self.file_listbox.curselection()) == self.file_listbox.size():
                self.file_listbox.selection_clear(0, tk.END)
            else:
                self.file_listbox.select_set(0, tk.END)

        # 右侧：全选按钮 (先 pack 右边，防止被左边挤出屏幕)
        btn_select_all = tk.Button(toolbar_frame, text="全选", command=toggle_select_all, 
                                   font=("微软雅黑", 10), bg="#eee", padx=10)
        btn_select_all.pack(side="right", anchor="e")

        # 左侧：错题控制区 (放入一个 Frame 整体靠左)
        mistake_frame = tk.Frame(toolbar_frame)
        mistake_frame.pack(side="left", fill="x")
        
        # 标签："错题" (红色) - 去掉"模式"二字以节省空间
        tk.Label(mistake_frame, text="错题", font=fonts["normal"], fg="#d32f2f").pack(side="left", padx=(0, 2))
        
        # 下拉框 1：操作符 (宽度6)
        self.combo_mistake_op = ttk.Combobox(mistake_frame, values=["不启用", ">=", "=="], 
                                             width=6, state="readonly", font=fonts["normal"])
        self.combo_mistake_op.pack(side="left", padx=2)
        
        # 读取配置
        op_mem = self.cfg.get("mistake_operator")
        self.combo_mistake_op.set(op_mem if op_mem in ["不启用", ">=", "=="] else "不启用")
        
        # 下拉框 2：次数 (宽度设为 3，够显示 999)
        self.combo_mistake_val = ttk.Combobox(mistake_frame, width=3, state="readonly", font=fonts["normal"])
        self.combo_mistake_val.pack(side="left", padx=2)
        
        # 标签："次"
        tk.Label(mistake_frame, text="次", font=fonts["normal"]).pack(side="left", padx=(0, 2))

        # 绑定保存配置事件
        def save_mistake_config(event):
            self.cfg.set("mistake_operator", self.combo_mistake_op.get())
            self.cfg.set("mistake_value", self.combo_mistake_val.get())
            
        self.combo_mistake_op.bind("<<ComboboxSelected>>", save_mistake_config)
        self.combo_mistake_val.bind("<<ComboboxSelected>>", save_mistake_config)
        
        # 列表框
        list_scroll = tk.Scrollbar(file_frame)
        list_scroll.pack(side="right", fill="y")
        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.MULTIPLE, 
                                        height=10,  # 这里控制文件框里显示的行数
                                        font=("Consolas", self.cfg.get("font_size_base")), 
                                        yscrollcommand=list_scroll.set,
                                        exportselection=False) # 防止点击别处时丢失勾选
        self.file_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.config(command=self.file_listbox.yview)

        # 2. 题型过滤
        filter_frame = tk.LabelFrame(main_frame, text="2. 题型过滤", font=fonts["normal"], padx=5, pady=5)
        filter_frame.pack(fill="x", pady=5)
        
        # 使用 Grid 网格布局 (2行2列)，防止单行排不下
        filter_frame.grid_columnconfigure(0, weight=1)
        filter_frame.grid_columnconfigure(1, weight=1)
        
        type_display = [('单选题', 'single'), ('多选题', 'multi'), ('判断题', 'judge'), ('填空题', 'fill')]
        for i, (txt, key) in enumerate(type_display):
            chk = tk.Checkbutton(filter_frame, text=txt, variable=self.filter_vars[key], font=fonts["normal"])
            # i//2 计算行号(0,0,1,1), i%2 计算列号(0,1,0,1)
            chk.grid(row=i//2, column=i%2, sticky="w", padx=10)

        # 3. 开始练习
        action_frame = tk.LabelFrame(main_frame, text="3. 开始练习", font=fonts["normal"], padx=5, pady=5)
        action_frame.pack(fill="x", pady=5)

        # 按钮去除固定宽度，使用 expand=True 自动填满
        tk.Button(action_frame, text="顺序练习", height=2, font=fonts["btn"], bg="#e3f2fd",
                  command=lambda: self.start_selected_practice(shuffle=False)).pack(side="left", expand=True, fill="x", padx=2)
        
        tk.Button(action_frame, text="随机练习", height=2, font=fonts["btn"], bg="#e3f2fd",
                  command=lambda: self.start_selected_practice(shuffle=True)).pack(side="left", expand=True, fill="x", padx=2)

        # 4. 模拟考试
        exam_frame = tk.LabelFrame(main_frame, text="4. 模拟考试", font=fonts["normal"], padx=5, pady=5)
        exam_frame.pack(fill="x", pady=5)

        # 按钮自动填满
        tk.Button(exam_frame, text="配置考试", height=2, bg="#fff9c4", font=fonts["btn"], 
                  command=self.show_exam_config_page).pack(side="left", expand=True, fill="x", padx=2)
        
        tk.Button(exam_frame, text="考试记录", height=2, bg="#f0f0f0", font=fonts["btn"], 
                  command=self.show_exam_history_page).pack(side="left", expand=True, fill="x", padx=2)
        
        if getattr(self, 'combo_repo', None):
            self.refresh_file_list()

    def refresh_file_list(self, event=None):
        if not getattr(self, 'combo_repo', None): return
        if not self.combo_repo.winfo_exists(): return

        current_repo = self.combo_repo.get()
        self.file_listbox.delete(0, tk.END)
        
        search_path = os.path.join("题库", current_repo, "*.txt")
        self.current_txt_paths = glob.glob(search_path) 
        
        # 定义自然排序的 key 函数
        def natural_key(text): 
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]
        
        # 对获取到的路径列表进行排序
        # 这里对 os.path.basename(p) 排序，即根据文件名排序，而不是全路径
        self.current_txt_paths.sort(key=lambda p: natural_key(os.path.basename(p)))
        
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

            # 根据模式执行全选或恢复记忆
            mode = self.cfg.get("file_selection_mode")
            last_repo = self.cfg.get("last_repo")
            last_files = self.cfg.get("last_files") or []

            # 模式A: 强制全选
            if mode == "all":
                self.file_listbox.select_set(0, tk.END)
            
            # 模式B: 记忆恢复 (只有当 repo 匹配时才恢复)
            elif mode == "remembered":
                if current_repo == last_repo:
                    missing_files = []
                    
                    for f_name in last_files:
                        if f_name in name_to_index:
                            self.file_listbox.select_set(name_to_index[f_name])
                        else:
                            missing_files.append(f_name)
                    
                    if missing_files:
                        msg = "以下上次选中的文件未找到（可能已被删除或重命名）：\n\n" + "\n".join(missing_files)
                        messagebox.showwarning("文件丢失提示", msg)
                else:
                    # 如果是“记忆模式”但切到了一个新题库（没有记忆），默认什么都不选
                    # 如果想在这里也默认全选，可以把下面的 pass 改成 self.file_listbox.select_set(0, tk.END)
                    pass 

            # 计算错题最大值
            local_max_err = 0
            if self.all_questions_cache:
                for q in self.all_questions_cache:
                    cnt = self.mistake_mgr.get_count(q.get_id())
                    if cnt > local_max_err: local_max_err = cnt
            
            # 更新第二个下拉框（次数）
            if getattr(self, 'combo_mistake_val', None) and self.combo_mistake_val.winfo_exists():
                # --- 改动开始：确保列表至少包含 "1"，并且从 1 开始到 max ---
                # 如果最大错误数是 0，也显示 1，方便用户预设
                limit = max(1, local_max_err) 
                vals = [str(i) for i in range(1, limit + 1)] 
                self.combo_mistake_val['values'] = vals
                # --- 改动结束 ---
                
                # 尝试恢复记忆的值
                mem_val = self.cfg.get("mistake_value")
                if mem_val in vals:
                    self.combo_mistake_val.set(mem_val)
                else:
                    # 如果记忆无效，默认选第1个（也就是 "1"）
                    if vals: self.combo_mistake_val.current(0)



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
            # 重新构建完整路径用于解析（如果没有缓存机制，就用这个；如果有all_questions_cache，就用下面的过滤）
            files = [os.path.join("题库", repo_dir, fname) for fname in selected_filenames]
        
        qs = QuestionParser.parse_target_files(files) 
        
        allowed = self.get_allowed_types()
        qs = [q for q in qs if q.q_type in allowed]
        
        op = self.combo_mistake_op.get()
        target_val_str = self.combo_mistake_val.get()
        
        if op != "不启用":
            if not target_val_str.isdigit():
                return messagebox.showwarning("提示", "请选择有效的错题次数！")
            
            target_val = int(target_val_str)
            filtered_qs = []
            
            for q in qs:
                err_count = self.mistake_mgr.get_count(q.get_id())
                if op == "==":
                    if err_count == target_val: filtered_qs.append(q)
                elif op == ">=":
                    if err_count >= target_val: filtered_qs.append(q)
            
            qs = filtered_qs
            
            if not qs:
                return messagebox.showinfo("提示", f"在所选文件中，没有找到符合“错误 {op} {target_val} 次”的题目。")
        
        if not qs: return messagebox.showerror("错误", "所选条件（文件/题型/错题）下没有题目！")
        self.start_quiz(qs, shuffle)

    def start_mistake_review(self):
        val = self.combo_mistake.get()
        if val in ["无", ""]: return
        
        # 获取列表框中选中的文件名
        idxs = self.file_listbox.curselection()
        if not idxs:
            messagebox.showwarning("提示", "请先在左侧列表中勾选要复习的题目文件！")
            return
        
        selected_files = set(self.file_listbox.get(i) for i in idxs)
        allowed = self.get_allowed_types()
        
        qs = []
        
        if val == "所有":
            # 筛选：属于选中文件 + 错误次数大于0 + 题型匹配
            qs = [
                q for q in self.all_questions_cache 
                if q.source_file in selected_files 
                and self.mistake_mgr.get_count(q.get_id()) > 0 
                and q.q_type in allowed
            ]
        else:
            # 筛选：属于选中文件 + 错误次数等于特定值 + 题型匹配
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



    # 考试配置页面
    
    def show_exam_config_page(self):
        # 1. 检查文件选择
        idxs = self.file_listbox.curselection()
        if not idxs: return messagebox.showwarning("提示", "请先在“1. 选择题目文件”中勾选作为考试范围的题库！")
        selected_files = [self.file_listbox.get(i) for i in idxs]
        
        # 2. 统计可用题数
        if getattr(self, 'combo_repo', None):
            repo_dir = self.combo_repo.get()
            files_path = [os.path.join("题库", repo_dir, fname) for fname in selected_files]
        else: return

        all_qs = QuestionParser.parse_target_files(files_path)
        type_counts = {'single': 0, 'multi': 0, 'judge': 0, 'fill': 0}
        for q in all_qs:
            if q.q_type in type_counts: type_counts[q.q_type] += 1
        
        # 3. 读取上次记忆的配置
        last_config = self.cfg.get("last_exam_settings") or {}

        # 4. 构建UI (上下滚动布局，适应手机)
        self.clear_window()
        fonts = self.get_fonts()
        
        # 顶部栏
        top_bar = tk.Frame(self.root, bg="#eee", pady=10); top_bar.pack(fill="x")
        tk.Button(top_bar, text="< 返回", command=self.setup_menu, font=fonts["ui"]).pack(side="left", padx=10)
        tk.Label(top_bar, text="考试配置", font=("微软雅黑", 16, "bold"), bg="#eee").pack(side="left", padx=10)

        # 滚动区域
        canvas = tk.Canvas(self.root, bg="white")
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg="white", padx=15, pady=15)

        scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        
        # 让内容宽度自适应屏幕
        def on_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_resize)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 题目参数设置 (使用 Grid)
        tk.Label(scroll_content, text="题目设置", font=fonts["title"], bg="white").pack(anchor="w", pady=(0, 10))
        
        grid_frame = tk.Frame(scroll_content, bg="white")
        grid_frame.pack(fill="x")
        
        # 设置列宽权重，保证拉伸
        for c in range(4): grid_frame.columnconfigure(c, weight=1)

        # 表头
        headers = ["题型", "可用", "考题数", "分值"]
        for i, h in enumerate(headers):
            tk.Label(grid_frame, text=h, font=("微软雅黑", 10, "bold"), fg="#555", bg="white").grid(row=0, column=i, pady=5)

        self.exam_entries = {}
        row = 1
        
        for q_type in ['single', 'multi', 'judge', 'fill']:
            t_name = self.type_map[q_type]
            avail = type_counts[q_type]
            
            # 题型名称
            tk.Label(grid_frame, text=t_name, font=fonts["normal"], bg="white").grid(row=row, column=0, pady=8)
            # 可用数量
            tk.Label(grid_frame, text=f"({avail})", font=fonts["ui"], fg="#888", bg="white").grid(row=row, column=1, pady=8)
            
            # 题目数量输入 (尝试加载记忆值)
            default_count = 0
            if q_type in last_config:
                default_count = int(last_config[q_type].get('count', 0))
            
            e_count = tk.Entry(grid_frame, width=5, font=fonts["normal"], justify="center", bg="#f5f5f5")
            e_count.insert(0, str(default_count))
            e_count.grid(row=row, column=2, pady=8)
            
            # 分值输入 (尝试加载记忆值)
            default_score = 1 if q_type=='single' else 2
            if q_type in last_config:
                default_score = float(last_config[q_type].get('score', default_score))

            e_score = tk.Entry(grid_frame, width=5, font=fonts["normal"], justify="center", bg="#f5f5f5")
            e_score.insert(0, str(default_score))
            e_score.grid(row=row, column=3, pady=8)
            
            self.exam_entries[q_type] = {'count': e_count, 'score': e_score, 'avail': avail}
            row += 1

        ttk.Separator(scroll_content, orient='horizontal').pack(fill='x', pady=20)

        # 时间设置
        time_frame = tk.Frame(scroll_content, bg="white")
        time_frame.pack(fill="x")
        
        tk.Label(time_frame, text="考试限时 (分钟):", font=fonts["normal"], bg="white").pack(side="left")
        
        # 尝试加载时间记忆
        last_time = last_config.get('time', 60)
        e_time = tk.Entry(time_frame, width=8, font=fonts["normal"], justify="center", bg="#f5f5f5")
        e_time.insert(0, str(last_time))
        e_time.pack(side="right")
        self.exam_entries['time'] = e_time

        ttk.Separator(scroll_content, orient='horizontal').pack(fill='x', pady=20)

        # 预设管理 (放在底部，横向拉通)
        tk.Label(scroll_content, text="预设管理:", font=fonts["ui"], bg="white", fg="#666").pack(anchor="w")
        
        preset_frame = tk.Frame(scroll_content, bg="white")
        preset_frame.pack(fill="x", pady=5)
        
        self.combo_presets = ttk.Combobox(preset_frame, values=self.exam_cfg_mgr.get_names(), state="readonly", font=fonts["ui"])
        self.combo_presets.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        def load_preset(event=None):
            name = self.combo_presets.get()
            data = self.exam_cfg_mgr.get_preset(name)
            if data:
                for qt in ['single', 'multi', 'judge', 'fill']:
                    self.exam_entries[qt]['count'].delete(0, tk.END); self.exam_entries[qt]['count'].insert(0, data.get(f"{qt}_c", 0))
                    self.exam_entries[qt]['score'].delete(0, tk.END); self.exam_entries[qt]['score'].insert(0, data.get(f"{qt}_s", 1))
                self.exam_entries['time'].delete(0, tk.END); self.exam_entries['time'].insert(0, data.get("time", 60))
        self.combo_presets.bind("<<ComboboxSelected>>", load_preset)

        # 保存预设按钮
        def save_preset_btn():
            name = simpledialog.askstring("保存配置", "请输入配置名称 (如: Config1):")
            if name:
                data = {}
                try:
                    for qt in ['single', 'multi', 'judge', 'fill']:
                        data[f"{qt}_c"] = int(self.exam_entries[qt]['count'].get())
                        data[f"{qt}_s"] = float(self.exam_entries[qt]['score'].get())
                    data["time"] = int(self.exam_entries['time'].get())
                    self.exam_cfg_mgr.save_preset(name, data)
                    self.combo_presets['values'] = self.exam_cfg_mgr.get_names()
                    messagebox.showinfo("成功", "配置已保存")
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数字")

        tk.Button(preset_frame, text="保存为预设", command=save_preset_btn, bg="#e0e0e0", font=fonts["ui"]).pack(side="right")

        # 开始考试
        def start_exam_check():
            final_qs = []
            score_map = {}
            total_score = 0
            
            # 准备要保存的配置数据
            current_settings = {}
            
            try:
                # 随机抽取题目
                for qt in ['single', 'multi', 'judge', 'fill']:
                    req_c = int(self.exam_entries[qt]['count'].get())
                    req_s = float(self.exam_entries[qt]['score'].get())
                    avail = self.exam_entries[qt]['avail']
                    
                    # 记录配置以便保存
                    current_settings[qt] = {'count': req_c, 'score': req_s}
                    
                    if req_c > avail:
                        messagebox.showwarning("数量不足", f"{self.type_map[qt]} 请求 {req_c} 题，但仅有 {avail} 题！")
                        return
                    
                    if req_c > 0:
                        pool = [q for q in all_qs if q.q_type == qt]
                        selected = random.sample(pool, req_c)
                        final_qs.extend(selected)
                        score_map[qt] = req_s
                        total_score += req_c * req_s
                
                limit_min = int(self.exam_entries['time'].get())
                current_settings['time'] = limit_min # 记录时间配置
                
                if limit_min <= 0: return messagebox.showwarning("提示", "时间必须大于0")
                if not final_qs: return messagebox.showwarning("提示", "未选择任何题目！")
                
                # 保存当前配置到 config.json，下次自动加载
                self.cfg.set("last_exam_settings", current_settings)

                # 初始化考试数据
                self.exam_mode = True
                self.exam_score_map = score_map 
                self.exam_total_time = limit_min * 60
                self.exam_start_timestamp = datetime.now()
                self.exam_end_time = time.time() + self.exam_total_time
                self.exam_answers = {} 
                
                
                self.current_repo_name = repo_dir 

                self.start_quiz(final_qs, shuffle=True)

            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字！")

        tk.Button(scroll_content, text="开始考试", command=start_exam_check, 
                  bg="#4caf50", fg="white", font=("微软雅黑", 14, "bold"), height=2).pack(fill="x", pady=30)
    

    def start_quiz(self, questions, shuffle):

        self.current_queue = list(questions)

        if shuffle: 
            random.shuffle(self.current_queue)
            
        # 定义排序优先级：单选(0) -> 多选(1) -> 判断(2) -> 填空(3)
        # 这保证了做题顺序和答题卡板块顺序一致
        type_priority = {'single': 0, 'multi': 1, 'judge': 2, 'fill': 3}
        
        # 执行排序
        self.current_queue.sort(key=lambda q: type_priority.get(q.q_type, 99))

        self.current_index = 0

        self.session_stats = {'total': 0, 'correct': 0}

        # 初始化答题卡状态 
        # key: 题目索引 (0, 1, 2...), value: True(对), False(错), None(未答)
        self.quiz_results = {} 

        # 考试模式下，初始化答案记录
        if self.exam_mode:
            self.exam_answers = {} # 重置答案
            self.update_exam_timer() # 启动计时器

        self.show_question_ui()

    # 倒计时
    def update_exam_timer(self):
        if not self.exam_mode: return
        
        remaining = int(self.exam_end_time - time.time())
        if remaining <= 0:
            self.finish_exam(auto_submit=True)
            return
            
        # 更新UI显示 (需要 show_question_ui 创建了 timer_label 才能更新)
        if hasattr(self, 'timer_label') and self.timer_label.winfo_exists():
            m, s = divmod(remaining, 60)
            color = "red" if remaining < 300 else "black" # 最后5分钟变红
            self.timer_label.config(text=f"剩余 {m:02d}:{s:02d}", fg=color)
            
        self.exam_timer_id = self.root.after(1000, self.update_exam_timer)
    
    def finish_exam(self, auto_submit=False):
        # 停止计时
        if self.exam_timer_id:
            self.root.after_cancel(self.exam_timer_id)
            self.exam_timer_id = None
            
        if not auto_submit:
            if not messagebox.askyesno("交卷", "确定要交卷吗？\n交卷后将无法修改答案。"):
                self.update_exam_timer() # 恢复计时
                return

        # 计算分数
        my_score = 0
        max_score = 0
        correct_count = 0
        
        details = [] # 用于以后可能的详细回顾
        
        for i, q in enumerate(self.current_queue):
            q_score = self.exam_score_map.get(q.q_type, 0)
            max_score += q_score
            
            user_ans = self.exam_answers.get(i, "")
            is_correct = False
            
            # 判分逻辑
            if q.q_type in ['single', 'judge']:
                is_correct = (user_ans == q.correct_answer)
            elif q.q_type == 'multi':
                # 这里的 user_ans 已经是排序后的字符串
                correct_sorted = "".join(sorted(list(q.correct_answer)))
                is_correct = (user_ans == correct_sorted)
            elif q.q_type == 'fill':
                is_correct = (user_ans == q.correct_answer)
                
            if is_correct:
                my_score += q_score
                correct_count += 1
            
            self.quiz_results[i] = is_correct # 用于答题卡显示红绿

        # 计算耗时
        used_time = int(self.exam_total_time - (self.exam_end_time - time.time()))
        if used_time < 0: used_time = self.exam_total_time # 防止超时负数
        
        # 保存记录
        rec = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "score": round(my_score, 1),
            "total_score": round(max_score, 1),
            "used_time": f"{used_time//60} 分 {used_time%60} 秒",
            "correct_num": correct_count,
            "total_num": len(self.current_queue)
        }
        self.exam_hist_mgr.add_record(self.current_repo_name, rec)
        
        self.exam_mode = False # 退出考试模式
        
        msg = f"考试结束！\n\n得分: {rec['score']} / {rec['total_score']}\n耗时: {rec['used_time']}\n正确率: {correct_count} / {len(self.current_queue)} = {correct_count / len(self.current_queue)}"
        messagebox.showinfo("成绩单", msg)
        self.setup_menu()

    def return_to_menu(self): 
        # 考试模式下拦截退出
        if self.exam_mode:
            if messagebox.askyesno("退出考试", "考试正在进行中！\n退出将被视为【放弃】，不保存成绩。\n确定退出吗？"):
                if self.exam_timer_id: self.root.after_cancel(self.exam_timer_id)
                self.exam_mode = False
                self.setup_menu()
            return

        need_confirm = self.cfg.get("confirm_exit")
        if need_confirm is None: need_confirm = True

        if need_confirm:
            if not messagebox.askyesno("退出", "确定要退出练习吗？\n目前的进度将丢失。"):
                return 

        self.setup_menu()

    def clear_window(self):
        for widget in self.root.winfo_children(): widget.destroy()

    def show_summary(self):
        total = self.session_stats['total']
        correct = self.session_stats['correct']
        acc = (correct / total * 100) if total > 0 else 0.0
        msg = f"练习完成！\n\n共答: {total} 题\n正确: {correct} 题\n正确率: {acc:.2f}%"
        messagebox.showinfo("结果结算", msg)
        self.setup_menu()


    def show_card_page(self, event=None):
        """显示答题卡页面（覆盖主窗口）"""
        self.clear_window()
        fonts = self.get_fonts()
        
        # 顶部返回栏
        top_bar = tk.Frame(self.root, bg="#eee", pady=10)
        top_bar.pack(fill="x", side="top")
        
        # 这个返回按钮直接回当前题目，不重置
        tk.Button(top_bar, text="< 返回答题", command=self.show_question_ui, font=fonts["ui"]).pack(side="left", padx=10)
        tk.Label(top_bar, text="答题卡", font=("微软雅黑", 14, "bold"), bg="#eee").pack(side="left", padx=10)

        # 滚动区域容器
        scroll_container = tk.Frame(self.root)
        scroll_container.pack(fill="both", expand=True)

        # 1. 先把滚动条塞进去，靠右，防止被挤没
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        # 2. 再放画布，填满剩余空间
        canvas = tk.Canvas(scroll_container)
        canvas.pack(side="left", fill="both", expand=True)

        # 3. 关联两者
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=canvas.yview)

        # 电脑鼠标滚轮支持
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # 绑定 Windows 滚轮
        canvas.bind("<MouseWheel>", _on_mousewheel)
        # 绑定 Linux/安卓 滚轮 (Pydroid有时候识别为 Button-4/5)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # 手机/Pydroid 触屏拖拽支持
        # 记录手指按下的位置
        canvas.bind("<Button-1>", lambda event: canvas.scan_mark(event.x, event.y))
        # 拖动时滚动
        canvas.bind("<B1-Motion>", lambda event: canvas.scan_dragto(event.x, event.y, gain=1))

        # 画布内容区域
        scroll_frame = tk.Frame(canvas)
        # 必须创建 window 才能随画布滚动
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        # 动态调整滚动范围
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        # 动态调整宽度 (防止内容太窄或太宽)
        def configure_window_width(event):
            canvas.itemconfig(canvas_window, width=event.width)

        scroll_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_window_width)

        content_box = tk.Frame(scroll_frame, padx=20, pady=20)
        content_box.pack(fill="both", expand=True)


        type_names = {'single': '单选题', 'multi': '多选题', 'judge': '判断题', 'fill': '填空题'}

        def jump_to(idx):
            self.current_index = idx
            self.show_question_ui() # 跳转后，重新加载题目页就是返回了

        # 按题型分组显示
        for q_type_key in ['single', 'multi', 'judge', 'fill']:
            idxs = [i for i, q in enumerate(self.current_queue) if q.q_type == q_type_key]
            if not idxs: continue
            
            tk.Label(content_box, text=type_names.get(q_type_key, q_type_key), 
                     font=("微软雅黑", 12, "bold"), anchor="w").pack(fill="x", pady=(10, 5))
            
            grid_frame = tk.Frame(content_box)
            grid_frame.pack(fill="x", pady=5)

            columns = 5 # 手机竖屏可能较窄，每行改为5个比较安全
            for i, global_idx in enumerate(idxs):
                res = self.quiz_results.get(global_idx)
                if res is None:
                    bg_color = "#e0e0e0" 
                    fg_color = "black"
                elif res is True:
                    bg_color = "#81c784" 
                    fg_color = "white"
                else:
                    bg_color = "#e57373"
                    fg_color = "white"
                
                bd_size = 1
                relief = "raised"
                if global_idx == self.current_index:
                    bd_size = 3
                    relief = "solid"
                    bg_color = "#64b5f6"

                btn = tk.Button(grid_frame, text=str(i + 1), width=4, 
                                bg=bg_color, fg=fg_color, relief=relief, bd=bd_size,
                                command=lambda idx=global_idx: jump_to(idx))
                btn.grid(row=i // columns, column=i % columns, padx=3, pady=3)

    def show_question_ui(self):
        self.clear_window()
        if self.current_index >= len(self.current_queue):
            if self.exam_mode:
                # 考试模式最后一题点下一题，不自动交卷，停留在最后一题或提示
                self.current_index -= 1
                messagebox.showinfo("提示", "已经是最后一题了，请检查后点击顶部“交卷”按钮。")
                self.show_question_ui()
                return
            else:
                self.show_summary()
                return

        q = self.current_q = self.current_queue[self.current_index]
        fonts = self.get_fonts()




        
        # 1. 顶部容器 (减小内边距 padx/pady 以节省空间)
        top_bar = tk.Frame(self.root, bg="#eee", pady=5, padx=5)
        top_bar.pack(fill="x", side="top")
        
        # 2. 左侧：返回按钮 (去掉 width 限制，让它自动适应 "< 主页" 的宽度)
        tk.Button(top_bar, text="< 主页", command=self.return_to_menu, 
                  font=fonts["ui"], bg="#ddd").pack(side="left", padx=(0, 5))
        
        # 3. 右侧容器 (优先 pack 右侧，保证不被挤掉)
        right_frame = tk.Frame(top_bar, bg="#eee")
        right_frame.pack(side="right") # 靠右停靠

        # === 核心修改部分开始 ===
        
        # 创建一个“上半行”容器，用来放 错误次数 和 来源文件
        # anchor="center" 确保它们居中，side="top" 放在 right_frame 的上面
        info_row = tk.Frame(right_frame, bg="#eee")
        info_row.pack(side="top", anchor="center") 

        # --- 右侧组件 2：错误次数 ---
        # 注意：这里要 pack 到 info_row 里面
        err_count = self.mistake_mgr.get_count(q.get_id())
        err_color = "#d32f2f" if err_count > 0 else "#999"
        tk.Label(info_row, text=f"错误 {err_count} ", bg="#eee", font=fonts["ui"], 
                 fg=err_color).pack(side="left", padx=2)

        # --- 右侧组件 3：来源文件 ---
        # 注意：这里也要 pack 到 info_row 里面
        f_name = q.source_file
        if len(f_name) > 8: f_name = f_name[:6] + ".."
        tk.Label(info_row, text=f"{f_name}", bg="#eee", font=fonts["ui"], 
                 fg="#666").pack(side="left", padx=2)

        # --- 右侧下半部分：倒计时 (仅考试模式显示) ---
        # 直接 pack 到 right_frame 里面，因为 info_row 占了上面，它自然会排在下面
        if self.exam_mode:
            self.timer_label = tk.Label(right_frame, text="剩余 --:--", font=("微软雅黑", 10, "bold"), 
                                      bg="#eee", fg="#1976d2")
            self.timer_label.pack(side="top", anchor="center", pady=(0, 0))



        # 4. 中间：进度 (填满剩余空间，居中显示)
        center_text = f"答题卡 {self.current_index + 1} / {len(self.current_queue)}"
        lbl_progress = tk.Label(top_bar, text=center_text, bg="#eee", fg="#1976d2",
                                cursor="hand2", font=("微软雅黑", fonts["ui"][1], "bold"))
        # 使用 pack fill=x 自动占据中间剩余空间
        lbl_progress.pack(side="left", fill="x", expand=True)
        lbl_progress.bind("<Button-1>", self.show_card_page)






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

        # 使用 Grid + uniform 强制按钮等宽 
        # 配置两列，权重相同(weight=1)，并指定 uniform 组名相同(比如 "nav")
        # 这样无论文字长短，两列的宽度都会被强制拉伸到一样宽（以较宽者为准）
        nav_frame.columnconfigure(0, weight=1, uniform="nav")
        nav_frame.columnconfigure(1, weight=1, uniform="nav")

        self.btn_prev = tk.Button(nav_frame, text="<< 上一题", command=self.prev_question, 
                                  font=fonts["btn"], width=15, height=2, bg="#e0e0e0")
        # grid 布局，sticky="ew" 表示横向拉伸填满格子
        self.btn_prev.grid(row=0, column=0, padx=5, sticky="ew") 
        
        self.btn_next = tk.Button(nav_frame, text="下一题 >>", command=self.next_question, 
                                  state="normal", font=fonts["btn"], width=15, height=2, bg="#2196f3", fg="white")
        self.btn_next.grid(row=0, column=1, padx=5, sticky="ew")

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
        
        
        self.lbl_question = tk.Text(content_box, font=fonts["title"], bg="white", fg="black",
                                    relief="flat", highlightthickness=0, wrap="char", height=1,
                                    spacing1=5, spacing3=5) # 文字内部行间距           
        
        self.lbl_question.insert("1.0", full_text)         
        self.lbl_question.configure(state="disabled")    

        # 增大 pady 的第二个值 (0, 30)，让题目和选项A拉开距离
        self.lbl_question.pack(fill="x", pady=(0, 30))   

        # 增加一个动态调整高度的函数
        # 因为 Text 组件默认不会像 Label 那样根据内容自动撑开高度，需要手动算
        def auto_height(event=None):
            # 获取组件现在的宽度对应的“显示行数”
            # count 方法返回 (行数, 像素高度...)，取第一个
            num_lines = self.lbl_question.count("1.0", "end", "displaylines")
            if num_lines:
                # 设置 Text 组件的高度为实际行数
                self.lbl_question.config(height=num_lines[0])

        # 绑定配置事件，当屏幕旋转或渲染完成时自动调整高度
        self.lbl_question.bind("<Configure>", auto_height)
        

        opts_frame = tk.Frame(content_box, bg="white")
        opts_frame.pack(fill="x", anchor="w")
        
        self.input_vars = [] 
        
        def auto_submit_if_enabled():
            if self.cfg.get("auto_submit") and self.btn_submit['state'] != 'disabled':
                self.check_answer()

        
        # 定义一个通用的高度自适应函数 (给选项用)
        def fit_height(event, widget):
            num_lines = widget.count("1.0", "end", "displaylines")
            if num_lines: widget.config(height=num_lines[0])

        if q.q_type in ['single', 'judge']:
            self.var_single = tk.StringVar(value="UNSELECTED_SAFE")
            
            for opt in q.options:
                # 每一行选项用一个 Frame 包裹，方便布局
                row_frame = tk.Frame(opts_frame, bg="white", pady=5)

                # 增加 pady=8，让选项与选项之间拉开距离
                row_frame.pack(fill="x", anchor="w", pady=8) 
                
                # 左边放单选圆点 (不带文字)
                # value=opt[0] 取出 "A" / "B" 等作为值
                rb = tk.Radiobutton(row_frame, variable=self.var_single, value=opt[0], 
                                    bg="white", activebackground="white", 
                                    tristatevalue="TRISTATE_SAFE",
                                    command=auto_submit_if_enabled)

                # 这样当文字有很多行时，圆点会在正中间
                rb.pack(side="left", anchor="center")
                
                # 右边放 Text 组件显示文字 (支持自动换行)
                # 增加 spacing 参数，优化多行选项的阅读体验
                txt_opt = tk.Text(row_frame, font=fonts["normal"], bg="white", fg="black",
                                  relief="flat", width=1, height=1, wrap="char", # wrap="char" 是防截断的关键
                                  spacing1=2, spacing3=2) 
                txt_opt.insert("1.0", opt)
                txt_opt.configure(state="disabled")
                txt_opt.pack(side="left", fill="x", expand=True, padx=(5, 0)) # 文字离圆点远一点
                
                # 绑定自适应高度
                txt_opt.bind("<Configure>", lambda e, w=txt_opt: fit_height(e, w))
                
                # 点击文字也能选中圆点
                def on_click_single(event, val=opt[0]):
                    if self.btn_submit['state'] == 'disabled': return # 已提交则不可点
                    self.var_single.set(val)
                    auto_submit_if_enabled()
                    
                txt_opt.bind("<Button-1>", on_click_single)

        elif q.q_type == 'multi':
            for opt in q.options:
                row_frame = tk.Frame(opts_frame, bg="white", pady=5)
                # <--- 修改3：增加 pady=8，让选项之间变宽
                row_frame.pack(fill="x", anchor="w", pady=8)
                
                var = tk.IntVar(value=0)
                self.input_vars.append((opt[0], var))
                
                # 左边放复选方框
                cb = tk.Checkbutton(row_frame, variable=var, onvalue=1, offvalue=0, 
                                    bg="white", activebackground="white")

                cb.pack(side="left", anchor="center")
                
                # 右边放 Text 组件
                txt_opt = tk.Text(row_frame, font=fonts["normal"], bg="white", fg="black",
                                  relief="flat", width=1, height=1, wrap="char",
                                  spacing1=2, spacing3=2)
                txt_opt.insert("1.0", opt)
                txt_opt.configure(state="disabled")
                txt_opt.pack(side="left", fill="x", expand=True, padx=(5, 0))
                
                txt_opt.bind("<Configure>", lambda e, w=txt_opt: fit_height(e, w))
                
                # 点击文字切换方框勾选
                def on_click_multi(event, v=var):
                    if self.btn_submit['state'] == 'disabled': return
                    current = v.get()
                    v.set(1 - current) # 0变1，1变0
                    
                txt_opt.bind("<Button-1>", on_click_multi)
                
                
        elif q.q_type == 'fill':
            tk.Label(opts_frame, text="请输入答案：", font=fonts["normal"], bg="white").pack(anchor="w")
            self.entry_fill = tk.Text(opts_frame, height=4, font=fonts["normal"])
            self.entry_fill.pack(anchor="w", pady=5, fill="x")

    # 用 Grid 网格布局，强制对齐 
    def show_exam_history_page(self):
        if not getattr(self, 'combo_repo', None): 
            messagebox.showinfo("提示", "请先选择一个题库！")
            return
        repo_name = self.combo_repo.get()
        records = self.exam_hist_mgr.get_records(repo_name)
        
        self.clear_window()
        fonts = self.get_fonts()
        
        # 顶部导航
        top_bar = tk.Frame(self.root, bg="#eee", pady=10)
        top_bar.pack(fill="x")
        tk.Button(top_bar, text="< 返回", command=self.setup_menu, font=fonts["ui"]).pack(side="left", padx=10)
        # 标题字号稍微改小一点，防止手机顶栏太挤
        tk.Label(top_bar, text=f"记录-{repo_name}", font=("微软雅黑", 12, "bold"), bg="#eee").pack(side="left", padx=5)

        # 列表容器
        list_frame = tk.Frame(self.root, padx=5, pady=5) # 减小边距以节省手机空间
        list_frame.pack(fill="both", expand=True)

        # 使用 Canvas 实现纵向滚动
        canvas = tk.Canvas(list_frame, bg="white")
        scroll = tk.Scrollbar(list_frame, command=canvas.yview)
        
        # 内容容器
        scroll_content = tk.Frame(canvas, bg="white")
        
        # 让 scroll_content 的宽度永远等于 canvas 的可视宽度
        # 这样 Grid 布局才能自动充满屏幕
        canvas_window = canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        
        def on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_resize)
        
        scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scroll.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Grid 布局配置
        # 定义5列，weight表示宽度比例。
        # 时间最长(3)，分数/总分短(1)，耗时中等(2)，正确率中等(2)
        columns_cfg = [
            ("时间", 3), 
            ("分数", 1), 
            ("总分", 1), 
            ("耗时", 2), 
            ("正确率", 2) 
        ]
        
        # 配置列权重，使其自动拉伸填满屏幕
        for col_idx, (_, weight) in enumerate(columns_cfg):
            scroll_content.columnconfigure(col_idx, weight=weight)

        # 绘制表头
        header_font = ("微软雅黑", 10, "bold") # 手机上字号适中
        for col_idx, (text, _) in enumerate(columns_cfg):
            lbl = tk.Label(scroll_content, text=text, font=header_font, 
                           bg="#ddd", fg="#333", pady=8, relief="flat")
            # sticky="nsew" 让标签填满格子
            lbl.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)

        # 绘制数据
        if not records:
            tk.Label(scroll_content, text="暂无考试记录", font=fonts["normal"], fg="#999", bg="white").grid(row=1, column=0, columnspan=5, pady=20)
        else:
            data_font = ("微软雅黑", 9) # 数据字号稍小
            for row_idx, rec in enumerate(records, start=1):
                
                short_date = rec['date'][5:] if len(rec['date']) > 5 else rec['date']
                
                vals = [
                    rec['date'], 
                    str(rec['score']), 
                    str(rec['total_score']), 
                    rec['used_time'], 
                    f"{rec['correct_num']} / {rec['total_num']} = {rec['correct_num']/rec['total_num']}"]
                
                
                bg_color = "#f9f9f9" if row_idx % 2 == 0 else "white"
                
                for col_idx, val in enumerate(vals):
                    lbl = tk.Label(scroll_content, text=val, font=data_font, 
                                   bg=bg_color, fg="#333", pady=8)
                    lbl.grid(row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=0)

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

        # 记录本题结果 
        self.quiz_results[self.current_index] = is_correct

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
        # 检查是否已经是最后一题
        # current_index 从0开始，所以 长度-1 就是最后一题的索引
        if self.current_index >= len(self.current_queue) - 1:
            
            if self.exam_mode:
                # 考试模式：弹出询问框
                if messagebox.askyesno("交卷提示", "已经是最后一题了，是否交卷？"):
                    # auto_submit=True 不再重复弹窗询问，直接结算
                    self.finish_exam(auto_submit=True)
                return
            
            else:
                # 练习模式：直接清空界面并显示结算
                self.clear_window()
                self.show_summary()
                return

        # 如果不是最后一题，正常跳转下一题
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
