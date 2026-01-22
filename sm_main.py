"""
Smart Backup - Ana Uygulama
Tarih: 19 Kasım 2025 
Yazar: Dr. Mustafa Afyonluoğlu

Gerekli Kütüphaneler:
    - customtkinter (pip install customtkinter)
    - tkinter (standart kütüphane)
    - sqlite3 (standart kütüphane)
    - os (standart kütüphane)
    - shutil (standart kütüphane)
    - glob (standart kütüphane)
    - datetime (standart kütüphane)
    - pathlib (standart kütüphane)
"""

import customtkinter as ctk
from tkinter import ttk, Menu, PanedWindow, VERTICAL
from typing import Optional
import webbrowser
import os

from sm_database import DatabaseManager
from sm_settings import SettingsManager
from sm_backup_engine import BackupEngine
from sm_ui_components import ConfirmDialog

# Mixin modülleri
from sm_project_mixin import ProjectMixin
from sm_mapping_mixin import MappingMixin
from sm_backup_mixin import BackupMixin


class SmartBackupApp(ctk.CTk, ProjectMixin, MappingMixin, BackupMixin):
    """Smart Backup Ana Uygulama"""
    
    def __init__(self):
        super().__init__()
        
        # Veritabanı ve ayarlar
        self.db = DatabaseManager()
        self.settings = SettingsManager(self.db)
        self.backup_engine = BackupEngine()
        
        # Tema ayarlarını uygula
        ctk.set_appearance_mode(self.settings.get_appearance_mode())
        ctk.set_default_color_theme(self.settings.get_theme())
        
        # Pencere ayarları
        self.title("Smart Backup - Akıllı Yedekleme Aracı")
        width, height = self.settings.get_window_size()
        self.geometry(f"{width}x{height}+100+10")
        # MUSTAFA self._center_window()
        
        # ESC tuşu ile kapat (onay ile)
        self.bind('<Escape>', lambda e: self._confirm_quit())
        
        # Seçili proje
        self.current_project_id: Optional[int] = None
        self.project_buttons = {}  # Proje butonlarını saklamak için
        
        # Erişilemeyen hedef sürücüler - {project_id: {mapping_id: [drive_list]}}
        self.inaccessible_drives = {}
        
        # Mevcut sürücü listesi - USB değişikliklerini algılamak için
        self._current_drives = self._get_available_drives()
        
        # Eşleştirme panosu (kopyala/yapıştır için)
        self.clipboard_mapping = None  # Panodaki eşleştirme verisi
        
        # Analiz sonuçları - yedekleme için kullanılacak
        self.analysis_results = None  # {mapping_id: {'files_to_backup': [...], 'excluded_files': [...]}}
        
        # Son yedekleme bilgisi - detay kaydetme için
        self.last_backup_id = None
        self.last_backup_files = None  # Yedeklenen dosyaların listesi
        
        self._create_widgets()
        self._load_projects()
        
        # Başlangıçta tüm projelerin hedef sürücülerini kontrol et
        self._check_all_target_drives()
        
        # Splitter konumunu yükle (pencere render edildikten sonra)
        self.after(100, self._apply_splitter_position)
        
        # Splitter konumu değiştiğinde kaydet
        self.bind('<ButtonRelease-1>', self._on_splitter_released)
        
        # Son seçilen projeyi yükle
        last_project_id = self.settings.get_last_project_id()
        if last_project_id > 0:
            self._select_project_by_id(last_project_id)
        
        # USB sürücü değişikliklerini izlemeyi başlat (her 2 saniyede kontrol)
        self._start_drive_monitor()
    
    def _center_window(self):
        """Pencereyi ekranda ortala"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """Widget'ları oluştur"""
        # Ana container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Sol panel - Proje listesi
        left_panel = ctk.CTkFrame(main_container, width=300)
        left_panel.pack(side="left", fill="both", pady=(0, 0), padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Proje listesi başlık
        project_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        project_header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(project_header, text="Projeler", 
                    font=("", 16, "bold")).pack(side="left")
        
        # Proje butonları
        project_buttons = ctk.CTkFrame(left_panel, fg_color="transparent")
        project_buttons.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(project_buttons, text="Yeni Proje", 
                     command=self._add_project, width=90).pack(side="left", padx=(0, 5))
        ctk.CTkButton(project_buttons, text="Düzenle", 
                     command=self._edit_project, width=80).pack(side="left", padx=(0, 5))
        ctk.CTkButton(project_buttons, text="Sil", 
                     command=self._delete_project, width=60,
                     fg_color="red", hover_color="darkred").pack(side="left")
        
        # Proje listesi
        list_frame = ctk.CTkFrame(left_panel)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.project_listbox = ctk.CTkScrollableFrame(list_frame)
        self.project_listbox.pack(fill="both", expand=True)
        
        # Proje listesi için context menü
        self.project_context_menu = Menu(self, 
                                        tearoff=0,
                                        background="#333333", 
                                        foreground="white", 
                                        activebackground="#1F6AA5"
                                         )
        self.project_context_menu.add_command(label="Proje Düzenle", command=self._edit_project)
        self.project_context_menu.add_command(label="Proje Sil", command=self._delete_project)
        self.project_context_menu.add_separator()
        self.project_context_menu.add_command(label="Proje Çoğalt", command=self._duplicate_project)

        list_font = ("Segoe UI", 13) 
        self.project_context_menu.config(font=list_font)    
        
        # Tema seçici - Sol panelin altında
        theme_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 0))
        
        ctk.CTkLabel(theme_frame, text="Tema:", font=("", 12)).pack(side="left", padx=(5, 5))
        self.appearance_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Light", "Dark", "System"],
            command=self._change_appearance,
            width=180
        )
        self.appearance_menu.set(self.settings.get_appearance_mode())
        self.appearance_menu.pack(side="left", padx=(0, 5))
        
        # Sağ panel - Eşleşmeler
        right_panel = ctk.CTkFrame(main_container)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Eşleşme başlık
        mapping_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        mapping_header.pack(fill="x", pady=(0, 10))
        
        self.mapping_title = ctk.CTkLabel(mapping_header, 
                                         text="Eşleşmeler (Proje seçin)",
                                         font=("", 16, "bold"))
        self.mapping_title.pack(side="left")
        
        # Eşleşme butonları
        mapping_buttons = ctk.CTkFrame(right_panel, fg_color="transparent")
        mapping_buttons.pack(fill="x", pady=(0, 10))
        
        self.add_mapping_btn = ctk.CTkButton(mapping_buttons, text="Yeni Eşleşme",
                                            command=self._add_mapping, width=110,
                                            state="disabled")
        self.add_mapping_btn.pack(side="left", padx=(0, 5))
        
        self.edit_mapping_btn = ctk.CTkButton(mapping_buttons, text="Düzenle",
                                             command=self._edit_mapping, width=80,
                                             state="disabled")
        self.edit_mapping_btn.pack(side="left", padx=(0, 5))
        
        self.delete_mapping_btn = ctk.CTkButton(mapping_buttons, text="Sil",
                                               command=self._delete_mapping, width=60,
                                               fg_color="red", hover_color="darkred",
                                               state="disabled")
        self.delete_mapping_btn.pack(side="left")
        
        # Yapıştır butonu - sadece panoda eşleştirme varsa görünecek
        self.paste_mapping_btn = ctk.CTkButton(mapping_buttons, text="Yapıştır",
                                               command=self._paste_mapping, width=80,
                                               fg_color="#FF8C00", hover_color="#FF6600")
        # Başlangıçta gizli - pack yapılmadı
        
        # PanedWindow - Eşleştirme tablosu ve Yedekleme detayları arasında splitter
        self.paned_window = PanedWindow(right_panel, orient=VERTICAL, 
                                        sashwidth=8, sashrelief="raised",
                                        bg="#3B8ED0")
        self.paned_window.pack(fill="both", expand=True, pady=(0, 5))
        
        # Üst panel - Eşleşme tablosu
        tree_frame = ctk.CTkFrame(self.paned_window)
        self.paned_window.add(tree_frame, minsize=100)
        
        # Scrollbar'lar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview için style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", 
                       fieldbackground="#ffebb4", borderwidth=0,
                       font=("Arial", 14),
                       rowheight=40)  # <-- Satır yüksekliğini arttırır (varsayılan ~20)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white",
                       font=("Arial", 15, "bold")) 
        
        style.map("Treeview.Heading",
                 background=[('active', '#5a5a5a')])  # Hover color for headers
        
        # Seçili satır renkleri - normal mavi, turuncu satırlar için ayrı işlenecek
        style.map("Treeview",
                 background=[('selected', '#1F6AA5')],  # Seçili satır mavi
                 foreground=[('selected', 'white')])

        # Treeview
        columns = ("ID", "Kaynak", "Filtre", "Hariç Tutulanlar", "Alt Klasörler", "Hedef")
        self.mapping_tree = ttk.Treeview(tree_frame, columns=columns, 
                                        show="headings",
                                        height=6,  # ←  (satır sayısı cinsinden)
                                        yscrollcommand=vsb.set,
                                        xscrollcommand=hsb.set)
        
        # Sütun başlıkları
        self.mapping_tree.heading("ID", text="ID")
        self.mapping_tree.heading("Kaynak", text="Kaynak Klasör")
        self.mapping_tree.heading("Filtre", text="Dosya")
        self.mapping_tree.heading("Hariç Tutulanlar", text="Hariç Tutulanlar")
        self.mapping_tree.heading("Alt Klasörler", text="Alt Klasörler")
        self.mapping_tree.heading("Hedef", text="Hedef Klasör")
        
        # Sütun genişlikleri
        self.mapping_tree.column("ID", width=50, stretch=False, anchor="center")
        self.mapping_tree.column("Kaynak", stretch=False, width=500)
        self.mapping_tree.column("Filtre", stretch=False, width=100)
        self.mapping_tree.column("Hariç Tutulanlar", stretch=False, width=180)
        self.mapping_tree.column("Alt Klasörler", stretch=False, width=100, anchor="center")
        self.mapping_tree.column("Hedef", stretch=False, width=700)
        
        # Scrollbar yapılandırması
        vsb.config(command=self.mapping_tree.yview)
        hsb.config(command=self.mapping_tree.xview)
        
        # Grid yerleşimi
        self.mapping_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Çift tıklama ile düzenle
        self.mapping_tree.bind('<Double-Button-1>', lambda e: self._edit_mapping())
        self.mapping_tree.bind("<<TreeviewSelect>>", self._on_mapping_select)
        
        # Eşleştirme listesi için context menü
        self.mapping_context_menu = Menu(self,
                                         tearoff=0,
                                         background="#333333", 
                                        foreground="white", 
                                        activebackground="#1F6AA5"
                                         )
        self.mapping_context_menu.add_command(label="Eşleştirme Düzenle", command=self._edit_mapping)
        self.mapping_context_menu.add_command(label="Sil", command=self._delete_mapping)
        self.mapping_context_menu.add_separator()
        self.mapping_context_menu.add_command(label="Çoğalt", command=self._duplicate_mapping)
        self.mapping_context_menu.add_command(label="Kopyala", command=self._copy_mapping)
        self.mapping_context_menu.add_separator()
        self.mapping_context_menu.add_command(label="Kaynak Klasörü Aç", command=self._open_source_folder)
        self.mapping_context_menu.add_command(label="Hedef Klasörü Aç", command=self._open_target_folder)
        self.mapping_context_menu.add_command(label="Revision'ları Aç", command=self._open_revisions_folder)
        self.mapping_context_menu.config(font=list_font)   

        # Sağ tık için binding
        self.mapping_tree.bind('<Button-3>', self._show_mapping_context_menu)
        
        # Alt panel - Log paneli (Yedekleme detayları)
        log_frame = ctk.CTkFrame(self.paned_window)
        self.paned_window.add(log_frame, minsize=100)
        
        log_label = ctk.CTkLabel(log_frame, text="Yedekleme Detayları",
                                font=("", 12, "bold"), anchor="w")
        log_label.pack(fill="x", padx=10, pady=(5, 0))
        
        # Scrollable text box
        self.log_textbox = ctk.CTkTextbox(log_frame, height=110, 
                                         font=("Arial", 12),
                                         wrap="word",
                                         fg_color="#000000",
                                         text_color="#FFFFFF")
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_textbox.configure(state="disabled")  # Read-only
        
        # İstatistik paneli
        stats_frame = ctk.CTkFrame(right_panel)
        stats_frame.pack(fill="x", pady=(0, 10))
        
        self.stats_label = ctk.CTkLabel(stats_frame, 
                                        text="İstatistikler: -",
                                        font=("", 12))
        self.stats_label.pack(pady=5)

        # Aksiyon butonları
        action_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        action_frame.pack(fill="x")
        
        self.calculate_btn = ctk.CTkButton(action_frame, text="Hesapla",
                                          command=self._calculate, width=100,
                                          state="disabled")
        self.calculate_btn.pack(side="left", padx=(0, 5))
        
        self.analyze_btn = ctk.CTkButton(action_frame, text="Analiz",
                                        command=self._analyze, width=100,
                                        state="disabled")
        self.analyze_btn.pack(side="left", padx=(0, 5))
        
        self.backup_btn = ctk.CTkButton(action_frame, text="Yedekle",
                                       command=self._backup, width=100,
                                       fg_color="green", hover_color="darkgreen",
                                       state="disabled")
        self.backup_btn.pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(action_frame, text="Geçmiş",
                     command=self._show_history, width=100).pack(side="left", padx=(0, 5))
        
        # Detayları Kaydet butonu - yedekleme tamamlandığında görünür olacak
        self.save_details_btn = ctk.CTkButton(action_frame, text="Detayları Kaydet",
                                             command=self._save_backup_file_details, width=120,
                                             fg_color="#FF8C00", hover_color="#FF6600")
        # Başlangıçta gizli - pack yapılmadı
        
        # Kapat butonu sağ alt
        ctk.CTkButton(action_frame, text="Kapat", command=self.quit,
                     width=100).pack(side="right")
        
        # Yardım butonu
        ctk.CTkButton(action_frame, text="❓ Yardım",
                     command=self._show_help, width=100,
                     fg_color="#6B7280", hover_color="#4B5563").pack(side="right", padx=(0, 5))
    
    def _apply_splitter_position(self):
        """Kaydedilmiş splitter konumunu uygula"""
        try:
            position = self.settings.get_splitter_position()
            self.update_idletasks()
            total_height = self.paned_window.winfo_height()
            if total_height > 0:
                sash_position = int(total_height * position)
                self.paned_window.sash_place(0, 0, sash_position)
        except Exception:
            pass  # İlk yüklemede hata olabilir
    
    def _on_splitter_released(self, event):
        """Splitter sürüklemesi bırakıldığında konumu kaydet"""
        try:
            # PanedWindow'un sash konumunu al
            sash_info = self.paned_window.sash_coord(0)
            if sash_info:
                sash_y = sash_info[1]
                total_height = self.paned_window.winfo_height()
                if total_height > 0:
                    position = sash_y / total_height
                    # Geçerli bir pozisyon ise kaydet (0.1 - 0.9 arası)
                    if 0.1 <= position <= 0.9:
                        self.settings.set_splitter_position(position)
        except Exception:
            pass  # Sash bulunamazsa hata olabilir
            
    def _change_appearance(self, mode: str):
        """Görünüm modunu değiştir"""
        ctk.set_appearance_mode(mode)
        self.settings.set_appearance_mode(mode)
    
    def _log_clear(self):
        """Log alanını temizle"""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
    
    def _log_write(self, message: str, color: str = None):
        """Log alanına mesaj yaz"""
        self.log_textbox.configure(state="normal")
        if color:
            # Renkli metin için tag kullan
            tag_name = f"color_{color}"
            self.log_textbox.tag_config(tag_name, foreground=color)
            self.log_textbox.insert("end", message + "\n", tag_name)
        else:
            self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")  # Otomatik scroll
        self.log_textbox.configure(state="disabled")
    
    def _check_all_target_drives(self):
        """Tüm projelerin hedef sürücülerinin erişilebilirliğini kontrol et"""
        self.inaccessible_drives = {}
        
        # Tüm projeleri al
        projects = self.db.get_all_projects()
        
        for project in projects:
            project_id = project['id']
            mappings = self.db.get_mappings_by_project(project_id)
            
            for mapping in mappings:
                target_path = mapping['target_path']
                mapping_id = mapping['id']
                
                # Hedef yoldan sürücü harfini al
                inaccessible = self._get_inaccessible_drives_from_path(target_path)
                
                if inaccessible:
                    if project_id not in self.inaccessible_drives:
                        self.inaccessible_drives[project_id] = {}
                    self.inaccessible_drives[project_id][mapping_id] = inaccessible
    
    def _get_inaccessible_drives_from_path(self, path: str) -> list:
        """Bir yolun içerdiği erişilemeyen sürücüleri döndür"""
        inaccessible = []
        
        if not path:
            return inaccessible
        
        # Yolun birden fazla hedef içerebileceğini düşün (virgülle ayrılmış olabilir)
        paths = [p.strip() for p in path.split(',')]
        
        for p in paths:
            if len(p) >= 2 and p[1] == ':':
                drive = p[0].upper() + ':'
                drive_path = drive + '\\'
                
                if not os.path.exists(drive_path):
                    if drive not in inaccessible:
                        inaccessible.append(drive)
        
        return inaccessible
    
    def _has_inaccessible_drives(self, project_id: int) -> bool:
        """Belirtilen projenin erişilemeyen sürücüleri var mı?"""
        return project_id in self.inaccessible_drives and len(self.inaccessible_drives[project_id]) > 0
    
    def _get_inaccessible_drives_for_mapping(self, project_id: int, mapping_id: int) -> list:
        """Belirtilen eşleştirmenin erişilemeyen sürücülerini döndür"""
        if project_id in self.inaccessible_drives:
            a = self.inaccessible_drives[project_id].get(mapping_id, [])
            # print(f"{mapping_id} için Erişilemeyen sürücüler bulundu: {a}")
            return self.inaccessible_drives[project_id].get(mapping_id, [])
        return []
    
    def _get_available_drives(self) -> set:
        """Sistemde mevcut olan sürücü harflerini döndür"""
        drives = set()
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                drives.add(letter)
        return drives
    
    def _start_drive_monitor(self):
        """USB sürücü değişikliklerini izlemeyi başlat"""
        self._check_drive_changes()
    
    def _check_drive_changes(self):
        """Sürücü değişikliklerini kontrol et"""
        try:
            new_drives = self._get_available_drives()
            
            # Değişiklik var mı kontrol et
            if new_drives != self._current_drives:
                # Sürücü listesini güncelle
                self._current_drives = new_drives
                
                # Hedef sürücü kontrolünü yeniden yap
                self._check_all_target_drives()
                
                # Eğer bir proje seçiliyse ekranı güncelle
                if self.current_project_id:
                    # Mevcut projeyi tekrar seç (başlık ve eşleştirmeleri güncellemek için)
                    project = self.db.get_project_by_id(self.current_project_id)
                    if project:
                        self._select_project(project)
        except Exception:
            pass  # Hata durumunda sessizce devam et
        
        # 2 saniye sonra tekrar kontrol et
        self.after(2000, self._check_drive_changes)
    
    def _on_mapping_select(self, event):
        """Eşleştirme seçildiğinde çağrılır"""
        self._update_mapping_buttons()
        self._update_mapping_selection_colors()
    
    def _update_mapping_selection_colors(self):
        """Seçili eşleştirme satırının rengini güncelle (turuncu satırlar için koyu turuncu)"""
        selection = self.mapping_tree.selection()
        
        # Tüm satırları dolaş ve renklerini ayarla
        for item in self.mapping_tree.get_children():
            tags = self.mapping_tree.item(item, 'tags')
            
            if item in selection:
                # Seçili satır
                if 'inaccessible' in tags:
                    # Turuncu satır seçili - koyu turuncu yap
                    self.mapping_tree.tag_configure('inaccessible_selected', 
                                                    background='#CC6600', foreground='white')
                    # Eski tag'i kaldır, yeni tag ekle
                    self.mapping_tree.item(item, tags=('inaccessible_selected',))
            else:
                # Seçili değil
                if 'inaccessible_selected' in tags:
                    # Koyu turuncudan normal turuncuya geri dön
                    self.mapping_tree.item(item, tags=('inaccessible',))
        
        # Tag konfigürasyonlarını güncelle
        self.mapping_tree.tag_configure('inaccessible', background='#FF8C00', foreground='black')
        self.mapping_tree.tag_configure('inaccessible_selected', background='#CC6600', foreground='white')
    
    def _confirm_quit(self):
        """Kapat onayı iste"""
        if ConfirmDialog.ask(self, "Kapat", "Uygulamayı kapatmak istediğinizden emin misiniz?"):
            self.quit()
    
    def _show_help(self):
        """Yardım dosyasını tarayıcıda aç"""
        # Yardım dosyasının tam yolunu bul
        help_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sm_help.html")
        
        if os.path.exists(help_file):
            # file:// protokolü ile aç
            webbrowser.open(f"file:///{help_file}")
        else:
            ConfirmDialog.show_warning(self, "Hata", f"Yardım dosyası bulunamadı:\n{help_file}")
    
    def quit(self):
        """Uygulamadan çık"""
        # Pencere boyutunu kaydet
        width = self.winfo_width()
        height = self.winfo_height()
        # MUSTAFA self.settings.set_window_size(width, height)
        
        # Veritabanını kapat
        self.db.close()
        
        # Uygulamayı kapat
        self.destroy()


def main():
    """Ana fonksiyon"""
    app = SmartBackupApp()
    app.mainloop()


if __name__ == "__main__":
    main()
