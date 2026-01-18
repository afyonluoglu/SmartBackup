import customtkinter as ctk
import os
from pathlib import Path
import string
import subprocess
import re
import win32com.client  # Windows COM için
import tkinter as tk
from tkinter import ttk, filedialog, Menu
import shutil
from threading import Thread

# Yüklenecek kütüphaneler: pywin32

class MobileFileExplorer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Mobil Telefon File Explorer")
        self.geometry("1400x800")
        
        # Tema ayarları
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Global değişkenler
        self.shell = None
        self.current_device = None
        self.device_list = []
        self.current_folder_object = None  # Şu anki klasörün COM objesi
        self.selected_files_info = []  # Seçili dosyaların bilgisi
        
        # Ana frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Üst panel - Cihaz seçimi
        self.top_frame = ctk.CTkFrame(self.main_frame)
        self.top_frame.pack(fill="x", padx=10, pady=10)
        
        self.label = ctk.CTkLabel(
            self.top_frame, 
            text="📱 Cihaz Seçin:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label.pack(side="left", padx=10)
        
        # Cihaz combobox
        self.drive_var = ctk.StringVar()
        self.drive_combo = ctk.CTkComboBox(
            self.top_frame,
            variable=self.drive_var,
            values=[],
            width=350,
            command=self.on_device_selected
        )
        self.drive_combo.pack(side="left", padx=10)
        
        # Yenile butonu
        self.refresh_btn = ctk.CTkButton(
            self.top_frame,
            text="🔄 Yenile",
            command=self.refresh_drives,
            width=100
        )
        self.refresh_btn.pack(side="left", padx=10)
        
        # Durum etiketi
        self.status_label = ctk.CTkLabel(
            self.top_frame,
            text="Cihaz bekleniyor...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=20)
        
        # Explorer frame - TreeView ve Tablo
        self.explorer_frame = ctk.CTkFrame(self.main_frame)
        self.explorer_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sol panel - TreeView (Klasör ağacı)
        self.tree_frame = ctk.CTkFrame(self.explorer_frame)
        self.tree_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.tree_label = ctk.CTkLabel(
            self.tree_frame,
            text="📁 Klasör Ağacı",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.tree_label.pack(pady=5)
        
        # TreeView için tk frame (ttk.Treeview kullanmak için)
        self.tree_container = tk.Frame(self.tree_frame, bg="#2b2b2b")
        self.tree_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar
        self.tree_scroll = ttk.Scrollbar(self.tree_container)
        self.tree_scroll.pack(side="right", fill="y")
        
        # TreeView
        self.folder_tree = ttk.Treeview(
            self.tree_container,
            yscrollcommand=self.tree_scroll.set,
            selectmode="browse"
        )
        self.folder_tree.pack(side="left", fill="both", expand=True)
        self.tree_scroll.config(command=self.folder_tree.yview)
        
        # TreeView stil
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            font=("Segoe UI", 14),
            rowheight=35)  # Satır yüksekliği - ikonlar için
        style.map("Treeview", background=[("selected", "#1f538d")])
        
        # TreeView bind
        self.folder_tree.bind("<<TreeviewSelect>>", self.on_folder_selected)
        self.folder_tree.bind("<<TreeviewOpen>>", self.on_folder_expanded)
        
        # Sağ panel - Dosya listesi
        self.file_list_frame = ctk.CTkFrame(self.explorer_frame)
        self.file_list_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.file_list_label = ctk.CTkLabel(
            self.file_list_frame,
            text="📄 Dosyalar ve Klasörler",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.file_list_label.pack(pady=5)
        
        # Dosya listesi için tk frame
        self.file_container = tk.Frame(self.file_list_frame, bg="#2b2b2b")
        self.file_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar
        self.file_scroll = ttk.Scrollbar(self.file_container)
        self.file_scroll.pack(side="right", fill="y")
        
        # Treeview for file list (with columns)
        self.file_list = ttk.Treeview(
            self.file_container,
            columns=("type", "size"),
            show="tree headings",
            yscrollcommand=self.file_scroll.set
        )
        self.file_list.pack(side="left", fill="both", expand=True)
        self.file_scroll.config(command=self.file_list.yview)
        
        # Kolonlar
        self.file_list.heading("#0", text="İsim")
        self.file_list.heading("type", text="Tür")
        self.file_list.heading("size", text="Boyut")
        
        self.file_list.column("#0", width=400, anchor="w")
        self.file_list.column("type", width=100, anchor="center")
        self.file_list.column("size", width=120, anchor="e")
        
        # Dosya listesi bind - çift tıklama ile klasöre giriş
        self.file_list.bind("<Double-1>", self.on_file_double_click)
        # Sağ tıklama menüsü için bind
        self.file_list.bind("<Button-3>", self.show_context_menu)
        
        # Context menu oluştur
        self.create_context_menu()
        
        # Başlangıçta cihazları yükle
        self.refresh_drives()
    
    def create_context_menu(self):
        """Sağ tıklama context menüsünü oluştur"""
        self.context_menu = Menu(self, 
                                 tearoff=0,
                                 background="#333333", 
                                foreground="white", 
                                activebackground="#1F6AA5"
                                 )
        self.context_menu.add_command(label="📋 Kopyala", command=self.copy_selected_files)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="ℹ️ Özellikler", command=self.show_file_properties)

        list_font = ("Segoe UI", 13) 
        self.context_menu.config(font=list_font)
    
    def show_context_menu(self, event):
        """Sağ tıklama menüsünü göster"""
        # Tıklanan öğeyi seç
        item = self.file_list.identify_row(event.y)
        if item:
            # Eğer öğe zaten seçili değilse, seç
            if item not in self.file_list.selection():
                self.file_list.selection_set(item)
            
            # Menüyü göster
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def copy_selected_files(self):
        """Seçili dosyaları bilgisayara kopyala"""
        selected = self.file_list.selection()
        if not selected:
            self.status_label.configure(text="❌ Dosya seçilmedi!")
            return
        
        # Hedef klasör seç
        dest_folder = filedialog.askdirectory(title="Dosyaları nereye kopyalamak istersiniz?")
        if not dest_folder:
            return
        
        # Seçili dosyaların bilgilerini topla
        files_to_copy = []
        
        for item_id in selected:
            item_text = self.file_list.item(item_id)["text"]
            item_type = self.file_list.item(item_id)["values"][0]
            
            # Sadece dosyaları kopyala (klasörleri atla)
            if item_type != "Klasör":
                file_name = item_text
                # İkonu temizle
                for icon in ['🎬', '🖼️', '🎵', '📄']:
                    file_name = file_name.replace(icon + " ", "")
                
                files_to_copy.append(file_name)
        
        if not files_to_copy:
            self.status_label.configure(text="⚠️ Kopyalanacak dosya yok (klasörler desteklenmiyor)")
            return
        
        # Kopyalama işlemini arka planda başlat
        self.status_label.configure(text=f"📂 {len(files_to_copy)} dosya kopyalanıyor...")
        Thread(target=self.copy_files_thread, args=(files_to_copy, dest_folder), daemon=True).start()
    
    def copy_files_thread(self, file_names, dest_folder):
        """Dosyaları arka planda kopyala"""
        try:
            if not self.current_folder_object:
                self.status_label.configure(text="❌ Kaynak klasör bulunamadı!")
                return
            
            # Hedef yolu normalize et (ters slash'e çevir)
            dest_folder = os.path.normpath(dest_folder)
            
            copied_count = 0
            failed_count = 0
            total = len(file_names)
            
            for idx, file_name in enumerate(file_names, 1):
                try:
                    # Kaynak dosyayı bul
                    source_item = None
                    for item in self.current_folder_object.Items():
                        if not item.IsFolder and item.Name == file_name:
                            source_item = item
                            break
                    
                    if not source_item:
                        print(f"Dosya bulunamadı: {file_name}")
                        failed_count += 1
                        continue
                    
                    # Durum güncelle
                    self.status_label.configure(text=f"📥 Kopyalanıyor ({idx}/{total}): {file_name[:30]}...")
                    
                    # MTP'den dosyayı kopyala - Shell FolderItem.CopyHere kullan
                    dest_folder_obj = self.shell.Namespace(dest_folder)
                    if dest_folder_obj:
                        # CopyHere: 16 = Otomatik evet yanıtı (üzerine yaz uyarısı gösterme)
                        dest_folder_obj.CopyHere(source_item, 16)
                        copied_count += 1
                        print(f"✓ Kopyalandı: #{copied_count} - {file_name}")
                    else:
                        failed_count += 1
                        print(f"✗ Hedef klasör açılamadı: {dest_folder}")
                        print(f"   Normalize edilmiş yol: {os.path.normpath(dest_folder)}")
                
                except Exception as e:
                    failed_count += 1
                    print(f"✗ Kopyalama hatası #{failed_count} - ({file_name}): {e}")
            
            # Sonuç
            if failed_count == 0:
                self.status_label.configure(text=f"✅ {copied_count} dosya başarıyla kopyalandı!")
                print("📁 Kopyalama tamamlandı.")
            else:
                self.status_label.configure(text=f"⚠️ {copied_count} başarılı, {failed_count} hatalı")
        
        except Exception as e:
            self.status_label.configure(text=f"❌ Kopyalama hatası: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_file_properties(self):
        """Seçili dosyanın özelliklerini göster"""
        selected = self.file_list.selection()
        if not selected or len(selected) > 1:
            self.status_label.configure(text="⚠️ Lütfen tek bir dosya seçin")
            return
        
        item_id = selected[0]
        item_text = self.file_list.item(item_id)["text"]
        item_values = self.file_list.item(item_id)["values"]
        
        # İkonu temizle
        for icon in ['🎬', '🖼️', '🎵', '📄', '📁']:
            item_text = item_text.replace(icon + " ", "")
        
        info = f"""📋 DOSYA ÖZELLİKLERİ

İsim: {item_text}
Tür: {item_values[0]}
Boyut: {item_values[1]}
"""
        
        # Basit bir bilgi penceresi
        from tkinter import messagebox
        messagebox.showinfo("Dosya Özellikleri", info)
        
    def get_mtp_devices(self):
        """MTP (Media Transfer Protocol) cihazlarını bul"""
        mtp_devices = []
        
        try:
            # PowerShell ile portable devices'ı listele
            ps_command = '''
            $shell = New-Object -ComObject Shell.Application
            $thisPC = $shell.Namespace(17)
            foreach ($item in $thisPC.Items()) {
                $name = $item.Name
                $path = $item.Path
                $type = $item.Type
                if ($path) {
                    Write-Output "$name|||$path|||$type"
                }
            }
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if '|||' in line:
                        parts = line.split('|||')
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            path = parts[1].strip()
                            item_type = parts[2].strip() if len(parts) > 2 else ""
                            
                            # MTP cihazları :: ile başlar veya Portable/Phone içerir
                            if (path.startswith('::') or 
                                'Portable' in item_type or 
                                'Phone' in name or
                                'Samsung' in name or
                                'S25' in name or
                                'Ultra' in name):
                                # Shell path yerine UNC path oluştur
                                unc_path = f"\\\\{name}"
                                mtp_devices.append({
                                    'name': name,
                                    'path': unc_path,
                                    'type': 'MTP'
                                })
            
            # Alternatif yöntem: WMI kullanarak
            if not mtp_devices:
                wmi_command = '''
                Get-PnpDevice -Class "WPD" -Status "OK" | Select-Object FriendlyName | ForEach-Object {
                    Write-Output $_.FriendlyName
                }
                '''
                
                result = subprocess.run(
                    ['powershell', '-Command', wmi_command],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        device_name = line.strip()
                        if device_name and device_name not in ['FriendlyName', '---', '']:
                            mtp_devices.append({
                                'name': device_name,
                                'path': f"\\\\{device_name}",
                                'type': 'MTP'
                            })
                            
        except Exception as e:
            print(f"MTP cihaz tarama hatası: {e}")
        
        return mtp_devices
    
    def get_available_drives(self):
        """Sistemdeki tüm kullanılabilir sürücüleri ve MTP cihazları listele"""
        devices = []
        
        # Normal sürücüler
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    # Sürücü okunabilir mi kontrol et
                    os.listdir(drive)
                    # Sürücü ismini al
                    try:
                        vol_info = subprocess.run(
                            ['cmd', '/c', 'vol', letter + ':'],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        vol_name = "Local Disk"
                        if vol_info.returncode == 0:
                            for line in vol_info.stdout.split('\n'):
                                if 'Volume in drive' in line:
                                    parts = line.split('is')
                                    if len(parts) > 1:
                                        vol_name = parts[1].strip()
                                    break
                        
                        devices.append({
                            'name': f"{vol_name} ({letter}:)",
                            'path': drive,
                            'type': 'DISK'
                        })
                    except:
                        devices.append({
                            'name': f"Disk ({letter}:)",
                            'path': drive,
                            'type': 'DISK'
                        })
                except:
                    pass
        
        # MTP cihazları ekle
        mtp_devices = self.get_mtp_devices()
        devices.extend(mtp_devices)
        
        return devices
    
    def refresh_drives(self):
        """Cihaz listesini yenile"""
        self.status_label.configure(text="Cihazlar taranıyor...")
        self.update()
        
        devices = self.get_available_drives()
        device_names = [f"[{d['type']}] {d['name']}" for d in devices]
        
        self.device_list = devices
        self.drive_combo.configure(values=device_names)
        
        if device_names:
            self.drive_combo.set(device_names[0])
            # İlk cihazı otomatik yükle
            self.on_device_selected(device_names[0])
        else:
            self.status_label.configure(text="❌ Cihaz bulunamadı")
    
    def on_device_selected(self, choice):
        """Cihaz seçildiğinde TreeView'i doldur"""
        self.status_label.configure(text=f"Yükleniyor: {choice}")
        self.update()
        
        # Seçilen cihazı bul
        selected_device = None
        for device in self.device_list:
            if f"[{device['type']}] {device['name']}" == choice:
                selected_device = device
                break
        
        if not selected_device:
            return
        
        self.current_device = selected_device
        print(f"Seçilen cihaz: {selected_device['name']} ({selected_device['type']})")
        device_type = selected_device['type']
        
        # TreeView'i temizle
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
        
        # Dosya listesini temizle
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        
        # Shell başlat
        try:
            if not self.shell:
                self.shell = win32com.client.Dispatch("Shell.Application")
            
            # DISK sürücüleri için
            if device_type == 'DISK':
                drive_path = selected_device['path']
                drive_name = selected_device['name']
                
                # Root ekle
                root_id = self.folder_tree.insert("", "end", text=f"💾 {drive_name}", values=(drive_name,), open=True)
                
                # Alt klasörleri yükle
                folder_obj = self.shell.Namespace(drive_path)
                if folder_obj:
                    self.load_subfolders(folder_obj, root_id)
                    self.folder_tree.selection_set(root_id)
                    self.load_folder_contents(folder_obj)
                
                self.status_label.configure(text=f"✅ {drive_name} yüklendi")
                return
            
            # MTP cihazları için
            this_pc = self.shell.Namespace(17)
            device_name = selected_device['name']
            
            # Cihazı bul
            target_device = None
            for item in this_pc.Items():
                if device_name.lower() in item.Name.lower():
                    target_device = item
                    break
            
            if not target_device:
                self.status_label.configure(text="❌ Cihaza erişilemedi")
                return
            
            # Root klasörü ekle (Dahili depolama)
            device_folder = target_device.GetFolder
            
            # İlk seviye klasörleri bul (Internal storage, Dahili depolama, vb.)
            root_added = False
            for item in device_folder.Items():
                if item.IsFolder:
                    folder_name = item.Name
                    # "Dahili depolama" veya "Internal storage" gibi ana depolamayı bul
                    if any(keyword in folder_name.lower() for keyword in ['dahili', 'internal', 'storage', 'phone']):
                        # TreeView'e root ekle - TAM ADINI KULLAN
                        root_id = self.folder_tree.insert("", "end", text=f"📱 {folder_name}", values=(folder_name,), open=True)
                        # Alt klasörleri yükle
                        self.load_subfolders(item.GetFolder, root_id)
                        root_added = True
                        # İlk klasörü seç
                        self.folder_tree.selection_set(root_id)
                        self.load_folder_contents(item.GetFolder)
                        mesaj = f"✅ {device_name} → {folder_name} yüklendi"
                        print(mesaj)
                        self.status_label.configure(text=mesaj)
                        break
            
            if not root_added:
                # Alternatif: Tüm klasörleri göster
                root_id = self.folder_tree.insert("", "end", text=f"📱 {device_name}", values=(device_name,), open=True)
                self.load_subfolders(device_folder, root_id)
                self.folder_tree.selection_set(root_id)
                self.load_folder_contents(device_folder)
                mesaj = f"✅ {device_name} → Tüm klasörler yüklendi"
                print(mesaj)
                self.status_label.configure(text=f"✅ {device_name} yüklendi")
            
        except Exception as e:
            self.status_label.configure(text=f"❌ Hata: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def load_subfolders(self, folder, parent_id):
        """Bir klasörün alt klasörlerini TreeView'e ekle"""
        try:
            subfolder_count = 0
            for item in folder.Items():
                try:
                    if item.IsFolder:
                        folder_name = item.Name
                        # Gizli/sistem klasörlerini atla
                        if not folder_name.startswith('.') and folder_name not in ['$RECYCLE.BIN', 'System Volume Information']:
                            # TAM KLASÖR ADINI values tuple'ında sakla
                            folder_id = self.folder_tree.insert(parent_id, "end", text=f"📁 {folder_name}", values=(folder_name,))
                            subfolder_count += 1
                            
                            # Alt klasör var mı kontrol et - lazy loading için dummy ekle
                            try:
                                has_subfolders = False
                                sub_count = 0
                                for subitem in item.GetFolder.Items():
                                    if subitem.IsFolder:
                                        has_subfolders = True
                                        break
                                    sub_count += 1
                                    if sub_count > 10:  # Performans için ilk 10'u kontrol et
                                        break
                                
                                if has_subfolders:
                                    # Dummy node ekle (lazy loading)
                                    self.folder_tree.insert(folder_id, "end", text="...", tags=("dummy",))
                            except:
                                pass
                except Exception as e:
                    print(f"Alt klasör ekleme hatası: {e}")
                    continue
            
            if subfolder_count == 0:
                # Klasör boş, hiç alt klasör yok
                pass
                
        except Exception as e:
            print(f"Subfolders yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def on_folder_expanded(self, event):
        """Klasör genişletildiğinde (ok tıklandığında) alt klasörleri yükle"""
        selected = self.folder_tree.selection()
        if not selected:
            # Eğer selection yoksa, focus olan item'ı al
            selected = [self.folder_tree.focus()]
        
        if not selected or not selected[0]:
            return
        
        item_id = selected[0]
        
        # Dummy node varsa alt klasörleri yükle
        children = self.folder_tree.get_children(item_id)
        if children and len(children) == 1 and self.folder_tree.item(children[0])["text"] == "...":
            # Dummy'yi kaldır ve gerçek klasörleri yükle
            self.folder_tree.delete(children[0])
            folder_path = self.get_folder_path_from_tree(item_id)
            
            self.status_label.configure(text="Alt klasörler yükleniyor...")
            self.update()
            
            try:
                folder_obj = self.get_folder_object(folder_path)
                if folder_obj:
                    self.load_subfolders(folder_obj, item_id)
                    self.status_label.configure(text="✅ Alt klasörler yüklendi")
                else:
                    self.status_label.configure(text="⚠️ Klasöre erişilemedi")
            except Exception as e:
                self.status_label.configure(text=f"❌ Hata: {str(e)}")
    
    def on_folder_selected(self, event):
        """TreeView'de klasör seçildiğinde"""
        selected = self.folder_tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        
        # Sağ panelde klasör içeriğini göster
        folder_path = self.get_folder_path_from_tree(item_id)
        
        self.status_label.configure(text="Klasör içeriği yükleniyor...")
        self.update()
        
        folder_obj = self.get_folder_object(folder_path)
        if folder_obj:
            self.load_folder_contents(folder_obj)
            # Yol bilgisini güncelle
            path_str = " → ".join(folder_path)
            self.file_list_label.configure(text=f"📄 İçerik: {path_str}")
            self.status_label.configure(text="✅ İçerik yüklendi")
        else:
            self.status_label.configure(text="⚠️ Klasöre erişilemedi")
    
    def get_folder_path_from_tree(self, item_id):
        """TreeView item'dan tam klasör yolunu oluştur"""
        path_parts = []
        current = item_id
        
        while current:
            item_values = self.folder_tree.item(current)["values"]
            # values tuple'ındaki tam klasör adını kullan
            if item_values and len(item_values) > 0:
                folder_name = item_values[0]
                if folder_name:  # Boş değilse
                    path_parts.insert(0, folder_name)
            current = self.folder_tree.parent(current)
        
        print(f"TreeView'den oluşturulan path: {path_parts}")
        return path_parts
    
    def get_folder_object(self, path_parts):
        """Klasör yolundan COM folder objesi al"""
        try:
            if not self.current_device:
                return None
            
            device_type = self.current_device['type']
            
            # DISK sürücüleri için - os.path kullan
            if device_type == 'DISK':
                # Normal disk için path oluştur
                full_path = self.current_device['path']
                for part in path_parts[1:]:  # İlk part sürücü adı
                    if part:
                        full_path = os.path.join(full_path, part)
                
                # Shell.Application ile folder objesi al
                return self.shell.Namespace(full_path)
            
            # MTP cihazları için - Shell COM kullan
            this_pc = self.shell.Namespace(17)
            device_name = self.current_device['name']
            
            # Cihazı bul
            target_device = None
            for item in this_pc.Items():
                if device_name.lower() in item.Name.lower():
                    target_device = item
                    break
            
            if not target_device:
                print(f"Cihaz bulunamadı: {device_name}")
                return None
            
            current_folder = target_device.GetFolder
            
            # Root mu? (sadece cihaz adı veya boş)
            if len(path_parts) == 0:
                return current_folder
            
            # İlk part "Dahili depolama" veya "Internal storage" gibi root storage'sa,
            # onu önce bulup oradan devam et
            first_part = path_parts[0] if len(path_parts) > 0 else None
            start_index = 0
            
            if first_part:
                # İlk klasörü bul (Dahili depolama gibi)
                found_root = False
                for item in current_folder.Items():
                    if item.IsFolder:
                        item_name = item.Name
                        if item_name == first_part or item_name.lower() == first_part.lower():
                            current_folder = item.GetFolder
                            found_root = True
                            start_index = 1  # Sonraki klasörden başla
                            print(f"  ✓ Root bulundu: {item_name}")
                            break
                
                if not found_root:
                    print(f"  ✗ Root klasör bulunamadı: {first_part}")
                    return None
            
            # Kalan path'i takip et
            for i, part in enumerate(path_parts[start_index:], start_index):
                if not part:
                    continue
                
                # Debug
                print(f"Aranan klasör [{i}]: '{part}'")
                
                found = False
                for item in current_folder.Items():
                    if item.IsFolder:
                        item_name = item.Name
                        # Tam eşleşme veya case-insensitive eşleşme
                        if item_name == part or item_name.lower() == part.lower():
                            current_folder = item.GetFolder
                            found = True
                            print(f"  ✓ Bulundu: {item_name}")
                            break
                
                if not found:
                    print(f"  ✗ Klasör bulunamadı: {part}")
                    print(f"  Mevcut klasörler:")
                    count = 0
                    for item in current_folder.Items():
                        if item.IsFolder:
                            print(f"    - {item.Name}")
                            count += 1
                            if count > 20:  # İlk 20 klasörü göster
                                print(f"    ... ve {current_folder.Items().Count - count} klasör daha")
                                break
                    return None
            
            return current_folder
            
        except Exception as e:
            print(f"Folder object alma hatası: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_folder_contents(self, folder):
        """Klasör içeriğini sağ panelde göster"""
        # Klasör objesini sakla (kopyalama için gerekli)
        self.current_folder_object = folder
        
        # Listeyi temizle
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        
        try:
            items = []
            
            for item in folder.Items():
                try:
                    item_name = item.Name
                    is_folder = item.IsFolder
                    
                    if is_folder:
                        items.append({
                            'name': item_name,
                            'type': 'Klasör',
                            'size': '',
                            'is_folder': True,
                            'icon': '📁'
                        })
                    else:
                        # Dosya boyutu
                        file_size = 0
                        try:
                            file_size = int(item.Size)
                        except:
                            pass
                        
                        file_ext = os.path.splitext(item_name)[1].lower()
                        file_type = self.get_file_type(file_ext)
                        
                        items.append({
                            'name': item_name,
                            'type': file_type,
                            'size': self.get_file_size(file_size) if file_size > 0 else '',
                            'is_folder': False,
                            'icon': self.get_file_icon(file_ext)
                        })
                except:
                    continue
            
            # Önce klasörler, sonra dosyalar
            items.sort(key=lambda x: (not x['is_folder'], x['name'].lower()))
            
            # Listeye ekle
            for item in items:
                self.file_list.insert("", "end", 
                    text=f"{item['icon']} {item['name']}", 
                    values=(item['type'], item['size']))
            
        except Exception as e:
            print(f"İçerik yükleme hatası: {e}")
    
    def get_file_type(self, ext):
        """Dosya uzantısından tür belirle"""
        video_ext = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        image_ext = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        audio_ext = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
        
        if ext in video_ext:
            return 'Video'
        elif ext in image_ext:
            return 'Resim'
        elif ext in audio_ext:
            return 'Ses'
        else:
            return 'Dosya'
    
    def get_file_icon(self, ext):
        """Dosya uzantısından ikon belirle"""
        video_ext = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        image_ext = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        audio_ext = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
        
        if ext in video_ext:
            return '🎬'
        elif ext in image_ext:
            return '🖼️'
        elif ext in audio_ext:
            return '🎵'
        else:
            return '📄'
    
    def on_file_double_click(self, event):
        """Dosya listesinde çift tıklama - klasöre gir"""
        selected = self.file_list.selection()
        if not selected:
            return
        
        item_id = selected[0]
        item_text = self.file_list.item(item_id)["text"]
        item_type = self.file_list.item(item_id)["values"][0]
        
        # Klasör mü?
        if item_type == "Klasör":
            folder_name = item_text.replace("📁 ", "")
            self.status_label.configure(text=f"Klasöre giriliyor: {folder_name}")
            
            # TreeView'de şu anki seçili klasörü bul
            tree_selected = self.folder_tree.selection()
            if not tree_selected:
                return
            
            current_item = tree_selected[0]
            
            # Seçili klasörün alt öğelerinde bu klasörü ara
            for child_id in self.folder_tree.get_children(current_item):
                child_text = self.folder_tree.item(child_id)["text"]
                child_name = child_text.replace("📁 ", "")
                
                if child_name == folder_name:
                    # Klasörü seç
                    self.folder_tree.selection_set(child_id)
                    self.folder_tree.see(child_id)  # Görünür yap
                    
                    # Eğer alt klasörleri varsa genişlet
                    children = self.folder_tree.get_children(child_id)
                    if children:
                        # Dummy var mı kontrol et
                        if self.folder_tree.item(children[0])["text"] == "...":
                            # Genişletme event'ini tetikle
                            self.folder_tree.item(child_id, open=True)
                            # Alt klasörleri yükle
                            self.on_folder_expanded(None)
                        else:
                            self.folder_tree.item(child_id, open=True)
                    
                    # Sağ paneli güncelle
                    self.on_folder_selected(None)
                    self.status_label.configure(text=f"✅ {folder_name} açıldı")
                    break
    
    def manual_scan(self):
        """Manuel tarama - artık kullanılmıyor"""
        pass
    
    def get_file_size(self, size_bytes):
        """Dosya boyutunu okunabilir formata çevir"""
        if size_bytes == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

if __name__ == "__main__":
    app = MobileFileExplorer()
    app.mainloop()
