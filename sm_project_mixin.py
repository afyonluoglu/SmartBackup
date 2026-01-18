"""
Smart Backup - Proje İşlemleri Mixin
Tarih: 3 Ocak 2026
Yazar: Dr. Mustafa Afyonluoğlu

Bu modül SmartBackupApp sınıfı için proje işlemlerini içerir.
"""

import customtkinter as ctk
from sm_ui_components import ProjectDialog, ConfirmDialog


class ProjectMixin:
    """Proje işlemleri için mixin sınıfı"""
    
    # ==================== PROJE İŞLEMLERİ ====================
    
    def _load_projects(self):
        """Projeleri listele"""
        # Mevcut widget'ları temizle
        for widget in self.project_listbox.winfo_children():
            widget.destroy()
        
        # Projeleri getir
        projects = self.db.get_all_projects()
        
        # Proje butonlarını saklamak için dict
        self.project_buttons = {}
        
        for project in projects:
            btn = ctk.CTkButton(
                self.project_listbox,
                text=project['name'],
                command=lambda p=project: self._select_project(p),
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30")
            )
            btn.pack(fill="x", pady=2)
            
            # Sağ tık için binding
            btn.bind('<Button-3>', lambda e, pid=project['id']: self._show_project_context_menu(e, pid))
            
            self.project_buttons[project['id']] = btn
        
        # Proje buton renklerini güncelle (erişilemeyen sürücüler için turuncu)
        self._update_project_button_colors()
    
    def _update_project_button_colors(self, selected_project_id: int = None):
        """Proje butonlarının renklerini güncelle (erişilemeyen sürücüler için turuncu)"""
        if selected_project_id is None:
            selected_project_id = self.current_project_id
        
        for proj_id, btn in self.project_buttons.items():
            has_inaccessible = self._has_inaccessible_drives(proj_id)
            
            if proj_id == selected_project_id:
                # Seçili proje
                if has_inaccessible:
                    # Seçili ve erişilemeyen sürücüsü var - koyu turuncu
                    btn.configure(fg_color=("#CC6600", "#994D00"))
                else:
                    # Seçili - normal vurgulu renk (mavi)
                    btn.configure(fg_color=("#3B8ED0", "#1F6AA5"))
            else:
                # Seçili değil
                if has_inaccessible:
                    # Erişilemeyen sürücüsü var - açık turuncu
                    btn.configure(fg_color=("#FF8C00", "#CC7000"))
                else:
                    # Normal renk - şeffaf
                    btn.configure(fg_color="transparent")
    
    def _select_project(self, project):
        """Proje seç"""
        self.current_project_id = project['id']
        self.settings.set_last_project_id(project['id'])
        
        # Analiz sonuçlarını sıfırla (proje değişti)
        self.analysis_results = None
        
        # Detayları Kaydet butonunu gizle (proje değişti)
        self._hide_save_details_button()
        
        # Proje butonlarını güncelle
        self._update_project_button_colors(selected_project_id=project['id'])
        
        # Başlığı güncelle - erişilemeyen sürücüleri de göster
        title_text = f"Eşleşmeler - {project['name']}"
        
        # Erişilemeyen sürücüleri kontrol et
        if self._has_inaccessible_drives(project['id']):
            # Tüm erişilemeyen sürücüleri topla
            all_inaccessible = set()
            for mapping_id, drives in self.inaccessible_drives[project['id']].items():
                all_inaccessible.update(drives)
            
            drives_str = ", ".join(sorted(all_inaccessible))
            # Kırmızı uyarı yazısı için ayrı label kullanmak yerine başlığa ekle
            title_text += f"   (Şu hedef sürücülere erişilemiyor: {drives_str})"
            # Başlık rengini kırmızı yap
            self.mapping_title.configure(text=title_text, text_color="#FF4444")
        else:
            self.mapping_title.configure(text=title_text, text_color=("gray10", "gray90"))
        
        # Butonları aktif et
        self.add_mapping_btn.configure(state="normal")
        self.calculate_btn.configure(state="normal")
        self.analyze_btn.configure(state="normal")
        self.backup_btn.configure(state="normal")
        
        # Eşleşmeleri yükle
        self._load_mappings()
    
    def _select_project_by_id(self, project_id: int):
        """ID ile proje seç"""
        project = self.db.get_project_by_id(project_id)
        if project:
            self._select_project(project)
    
    def _add_project(self):
        """Yeni proje ekle"""
        dialog = ProjectDialog(self, "Yeni Proje")
        self.wait_window(dialog)
        
        if dialog.result:
            name, desc = dialog.result
            try:
                project_id = self.db.add_project(name, desc)
                self._load_projects()
                self._select_project_by_id(project_id)
                ConfirmDialog.show_info(self, "Başarılı", "Proje başarıyla oluşturuldu.")
            except Exception as e:
                ConfirmDialog.show_error(self, "Hata", f"Proje oluşturulamadı: {str(e)}")
    
    def _edit_project(self):
        """Proje düzenle"""
        if not self.current_project_id:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir proje seçin!")
            return
        
        project = self.db.get_project_by_id(self.current_project_id)
        dialog = ProjectDialog(self, "Proje Düzenle", 
                              project['name'], project['description'])
        self.wait_window(dialog)
        
        if dialog.result:
            name, desc = dialog.result
            try:
                self.db.update_project(self.current_project_id, name, desc)
                self._load_projects()
                self._select_project_by_id(self.current_project_id)
                ConfirmDialog.show_info(self, "Başarılı", "Proje başarıyla güncellendi.")
            except Exception as e:
                ConfirmDialog.show_error(self, "Hata", f"Proje güncellenemedi: {str(e)}")
    
    def _delete_project(self):
        """Proje sil"""
        if not self.current_project_id:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir proje seçin!")
            return
        
        project = self.db.get_project_by_id(self.current_project_id)
        
        if not ConfirmDialog.ask(self, "Onay",
                                f"'{project['name']}' projesini ve tüm eşleşmelerini "
                                f"silmek istediğinizden emin misiniz?"):
            return
        
        self.db.delete_project(self.current_project_id)
        self.current_project_id = None
        self._load_projects()
        self._clear_mappings()
        ConfirmDialog.show_info(self, "Başarılı", "Proje başarıyla silindi.")
    
    def _duplicate_project(self):
        """Proje ve eşleştirmelerini çoğalt"""
        if not self.current_project_id:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir proje seçin!")
            return
        
        # Mevcut projeyi al
        project = self.db.get_project_by_id(self.current_project_id)
        
        # Yeni isim iste
        dialog = ProjectDialog(self, "Proje Çoğalt", 
                              f"{project['name']} (Kopya)", project['description'])
        self.wait_window(dialog)
        
        if dialog.result:
            name, desc = dialog.result
            try:
                # Yeni proje oluştur
                new_project_id = self.db.add_project(name, desc)
                
                # Eski projenin eşleştirmelerini al
                mappings = self.db.get_mappings_by_project(self.current_project_id)
                
                # Eşleştirmeleri yeni projeye kopyala
                for mapping in mappings:
                    self.db.add_mapping(
                        new_project_id,
                        mapping['source_path'],
                        mapping['file_filter'],
                        mapping.get('exclude_filter', ''),
                        bool(mapping['include_subdirs']),
                        mapping['target_path']
                    )
                
                self._load_projects()
                self._select_project_by_id(new_project_id)
                ConfirmDialog.show_info(self, "Başarılı", 
                                       f"Proje ve {len(mappings)} eşleştirme başarıyla çoğaltıldı.")
            except Exception as e:
                ConfirmDialog.show_error(self, "Hata", f"Proje çoğaltılamadı: {str(e)}")
    
    def _show_project_context_menu(self, event, project_id):
        """Proje context menüsünü göster"""
        # Önce projeyi seç
        self._select_project_by_id(project_id)
        
        # Context menüyü göster
        try:
            self.project_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.project_context_menu.grab_release()
