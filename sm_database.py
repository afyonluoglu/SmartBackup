"""
Smart Backup - Database Manager
Tarih: 19 Kasım 2025
Yazar: Dr. Mustafa Afyonluoğlu

Gerekli Kütüphaneler:
    - sqlite3 (standart kütüphane)
    - os (standart kütüphane)
    - datetime (standart kütüphane)
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class DatabaseManager:
    """Veritabanı işlemlerini yöneten sınıf"""
    
    def __init__(self):
        """Veritabanı bağlantısını başlatır"""
        # Veritabanı dosyasını py dosyasının bulunduğu dizinde oluştur
        self.db_path = os.path.join(os.path.dirname(__file__), 'smartbackup.db')
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Veritabanına bağlan"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Dictionary-like access
        self.cursor = self.conn.cursor()
    
    def _create_tables(self):
        """Gerekli tabloları oluştur"""
        # Projeler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_date TEXT NOT NULL,
                last_modified TEXT NOT NULL
            )
        ''')
        
        # Eşleşmeler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                source_path TEXT NOT NULL,
                file_filter TEXT NOT NULL,
                exclude_filter TEXT DEFAULT '',
                include_subdirs INTEGER DEFAULT 1,
                target_path TEXT NOT NULL,
                created_date TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        ''')
        
        # Eski veritabanlarına exclude_filter kolonu ekle
        try:
            self.cursor.execute("SELECT exclude_filter FROM mappings LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE mappings ADD COLUMN exclude_filter TEXT DEFAULT ''")
        
        # Yedekleme geçmişi tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                backup_date TEXT NOT NULL,
                analysis_duration_seconds REAL DEFAULT 0,
                duration_seconds REAL NOT NULL,
                total_files_copied INTEGER DEFAULT 0,
                total_files_moved_to_revisions INTEGER DEFAULT 0,
                total_files_skipped INTEGER DEFAULT 0,
                total_files_deleted_to_revisions INTEGER DEFAULT 0,
                total_size_copied INTEGER DEFAULT 0,
                total_size_moved INTEGER DEFAULT 0,
                total_size_skipped INTEGER DEFAULT 0,
                total_size_deleted INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        ''')
        
        # Eski veritabanlarına analysis_duration_seconds kolonu ekle
        try:
            self.cursor.execute("SELECT analysis_duration_seconds FROM backup_history LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE backup_history ADD COLUMN analysis_duration_seconds REAL DEFAULT 0")
        
        try:
            self.cursor.execute("SELECT total_files_deleted_to_revisions FROM backup_history LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE backup_history ADD COLUMN total_files_deleted_to_revisions INTEGER DEFAULT 0")
        
        try:
            self.cursor.execute("SELECT total_size_deleted FROM backup_history LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE backup_history ADD COLUMN total_size_deleted INTEGER DEFAULT 0")
        
        # Hariç tutulan dosyalar için kolonlar ekle
        try:
            self.cursor.execute("SELECT total_files_excluded FROM backup_history LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE backup_history ADD COLUMN total_files_excluded INTEGER DEFAULT 0")
        
        try:
            self.cursor.execute("SELECT total_size_excluded FROM backup_history LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE backup_history ADD COLUMN total_size_excluded INTEGER DEFAULT 0")
        
        # Yedekleme detayları tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_id INTEGER NOT NULL,
                mapping_id INTEGER NOT NULL,
                files_copied INTEGER DEFAULT 0,
                files_moved INTEGER DEFAULT 0,
                files_skipped INTEGER DEFAULT 0,
                files_deleted INTEGER DEFAULT 0,
                size_copied INTEGER DEFAULT 0,
                size_moved INTEGER DEFAULT 0,
                size_skipped INTEGER DEFAULT 0,
                size_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (backup_id) REFERENCES backup_history(id) ON DELETE CASCADE,
                FOREIGN KEY (mapping_id) REFERENCES mappings(id) ON DELETE CASCADE
            )
        ''')
        
        # Eski veritabanlarına yeni kolonları ekle
        try:
            self.cursor.execute("SELECT files_deleted FROM backup_details LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE backup_details ADD COLUMN files_deleted INTEGER DEFAULT 0")
        
        try:
            self.cursor.execute("SELECT size_deleted FROM backup_details LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE backup_details ADD COLUMN size_deleted INTEGER DEFAULT 0")
        
        # Hariç tutulan dosyalar için kolonlar ekle (backup_details)
        try:
            self.cursor.execute("SELECT files_excluded FROM backup_details LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE backup_details ADD COLUMN files_excluded INTEGER DEFAULT 0")
        
        try:
            self.cursor.execute("SELECT size_excluded FROM backup_details LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE backup_details ADD COLUMN size_excluded INTEGER DEFAULT 0")
        
        # Yedekleme dosya detayları tablosu (her dosyanın detayı)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_file_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_id INTEGER NOT NULL,
                mapping_id INTEGER,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                previous_size INTEGER DEFAULT NULL,
                backup_reason TEXT NOT NULL,
                FOREIGN KEY (backup_id) REFERENCES backup_history(id) ON DELETE CASCADE
            )
        ''')
        
        # Eski veritabanlarına previous_size kolonunu ekle
        try:
            self.cursor.execute("SELECT previous_size FROM backup_file_details LIMIT 1")
            # print("DEBUG: previous_size kolonu mevcut")
        except sqlite3.OperationalError:
            # print("DEBUG: previous_size kolonu ekleniyor...")
            self.cursor.execute("ALTER TABLE backup_file_details ADD COLUMN previous_size INTEGER DEFAULT NULL")
            self.conn.commit()
            # print("DEBUG: previous_size kolonu eklendi")
        
        # Eski veritabanlarına mapping_id kolonunu ekle
        try:
            self.cursor.execute("SELECT mapping_id FROM backup_file_details LIMIT 1")
            # print("DEBUG: mapping_id kolonu mevcut")
        except sqlite3.OperationalError:
            #print("DEBUG: mapping_id kolonu ekleniyor...")
            self.cursor.execute("ALTER TABLE backup_file_details ADD COLUMN mapping_id INTEGER")
            self.conn.commit()
            # print("DEBUG: mapping_id kolonu eklendi")
        
        # Ayarlar tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Analiz seçimleri tablosu - Her proje için son seçilen mapping'leri saklar
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_selections (
                project_id INTEGER PRIMARY KEY,
                mapping_ids TEXT NOT NULL,
                show_backup_files INTEGER DEFAULT 1,
                show_user_excluded_files INTEGER DEFAULT 1,
                show_hidden_excluded_files INTEGER DEFAULT 1,
                show_skipped_files INTEGER DEFAULT 1,
                show_revision_files INTEGER DEFAULT 1,
                show_deleted_files INTEGER DEFAULT 1,
                max_files_to_show INTEGER DEFAULT 50,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        ''')
        
        # Eski veritabanlarına yeni kolonları ekle
        try:
            self.cursor.execute("SELECT show_backup_files FROM analysis_selections LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE analysis_selections ADD COLUMN show_backup_files INTEGER DEFAULT 1")
        
        try:
            self.cursor.execute("SELECT show_user_excluded_files FROM analysis_selections LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE analysis_selections ADD COLUMN show_user_excluded_files INTEGER DEFAULT 1")
        
        try:
            self.cursor.execute("SELECT show_hidden_excluded_files FROM analysis_selections LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE analysis_selections ADD COLUMN show_hidden_excluded_files INTEGER DEFAULT 1")
        
        try:
            self.cursor.execute("SELECT show_skipped_files FROM analysis_selections LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE analysis_selections ADD COLUMN show_skipped_files INTEGER DEFAULT 1")
        
        try:
            self.cursor.execute("SELECT show_revision_files FROM analysis_selections LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE analysis_selections ADD COLUMN show_revision_files INTEGER DEFAULT 1")
        
        try:
            self.cursor.execute("SELECT max_files_to_show FROM analysis_selections LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE analysis_selections ADD COLUMN max_files_to_show INTEGER DEFAULT 50")
        
        try:
            self.cursor.execute("SELECT show_deleted_files FROM analysis_selections LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE analysis_selections ADD COLUMN show_deleted_files INTEGER DEFAULT 1")
        
        self.conn.commit()
    
    # ==================== PROJE İŞLEMLERİ ====================
    
    def add_project(self, name: str, description: str = "") -> int:
        """Yeni proje ekle"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO projects (name, description, created_date, last_modified)
            VALUES (?, ?, ?, ?)
        ''', (name, description, now, now))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_all_projects(self) -> List[Dict]:
        """Tüm projeleri getir"""
        self.cursor.execute('SELECT * FROM projects ORDER BY name')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_project_by_id(self, project_id: int) -> Optional[Dict]:
        """ID'ye göre proje getir"""
        self.cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def update_project(self, project_id: int, name: str, description: str = ""):
        """Proje güncelle"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            UPDATE projects 
            SET name = ?, description = ?, last_modified = ?
            WHERE id = ?
        ''', (name, description, now, project_id))
        self.conn.commit()
    
    def delete_project(self, project_id: int):
        """Proje sil (cascade ile eşleşmeler de silinir)"""
        self.cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        self.conn.commit()
    
    # ==================== EŞLEŞME İŞLEMLERİ ====================
    
    def add_mapping(self, project_id: int, source_path: str, file_filter: str,
                    exclude_filter: str, include_subdirs: bool, target_path: str) -> int:
        """Yeni eşleşme ekle"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO mappings (project_id, source_path, file_filter, exclude_filter,
                                  include_subdirs, target_path, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (project_id, source_path, file_filter, exclude_filter, 
              1 if include_subdirs else 0, target_path, now))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_mappings_by_project(self, project_id: int) -> List[Dict]:
        """Projeye ait tüm eşleşmeleri getir"""
        self.cursor.execute('''
            SELECT * FROM mappings WHERE project_id = ? ORDER BY id
        ''', (project_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_mapping_by_id(self, mapping_id: int) -> Optional[Dict]:
        """ID'ye göre eşleşme getir"""
        self.cursor.execute('SELECT * FROM mappings WHERE id = ?', (mapping_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def update_mapping(self, mapping_id: int, source_path: str, file_filter: str,
                       exclude_filter: str, include_subdirs: bool, target_path: str):
        """Eşleşme güncelle"""
        self.cursor.execute('''
            UPDATE mappings 
            SET source_path = ?, file_filter = ?, exclude_filter = ?, include_subdirs = ?, target_path = ?
            WHERE id = ?
        ''', (source_path, file_filter, exclude_filter, 1 if include_subdirs else 0, 
              target_path, mapping_id))
        self.conn.commit()
    
    def delete_mapping(self, mapping_id: int):
        """Eşleşme sil"""
        self.cursor.execute('DELETE FROM mappings WHERE id = ?', (mapping_id,))
        self.conn.commit()
    
    # ==================== YEDEKLEMe GEÇMİŞİ İŞLEMLERİ ====================
    
    def add_backup_history(self, project_id: int, analysis_duration_seconds: float,
                          duration_seconds: float,
                          total_files_copied: int, total_files_moved: int,
                          total_files_skipped: int, total_files_deleted: int,
                          total_files_excluded: int,
                          total_size_copied: int, total_size_moved: int,
                          total_size_skipped: int, total_size_deleted: int,
                          total_size_excluded: int,
                          status: str) -> int:
        """Yedekleme geçmişi ekle"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO backup_history 
            (project_id, backup_date, analysis_duration_seconds, duration_seconds, total_files_copied,
             total_files_moved_to_revisions, total_files_skipped, total_files_deleted_to_revisions,
             total_files_excluded, total_size_copied, total_size_moved, total_size_skipped, 
             total_size_deleted, total_size_excluded, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (project_id, now, analysis_duration_seconds, duration_seconds, total_files_copied,
              total_files_moved, total_files_skipped, total_files_deleted, total_files_excluded,
              total_size_copied, total_size_moved, total_size_skipped, total_size_deleted, 
              total_size_excluded, status))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_backup_detail(self, backup_id: int, mapping_id: int,
                         files_copied: int, files_moved: int, files_skipped: int,
                         files_deleted: int, files_excluded: int,
                         size_copied: int, size_moved: int,
                         size_skipped: int, size_deleted: int, size_excluded: int):
        """Yedekleme detayı ekle"""
        self.cursor.execute('''
            INSERT INTO backup_details
            (backup_id, mapping_id, files_copied, files_moved, files_skipped, files_deleted,
             files_excluded, size_copied, size_moved, size_skipped, size_deleted, size_excluded)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (backup_id, mapping_id, files_copied, files_moved, files_skipped, files_deleted,
              files_excluded, size_copied, size_moved, size_skipped, size_deleted, size_excluded))
        self.conn.commit()
    
    def get_all_backup_history(self) -> List[Dict]:
        """Tüm yedekleme geçmişini getir"""
        self.cursor.execute('''
            SELECT bh.*, p.name as project_name
            FROM backup_history bh
            JOIN projects p ON bh.project_id = p.id
            ORDER BY bh.backup_date DESC
        ''')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_backup_history_by_project(self, project_id: int) -> List[Dict]:
        """Projeye ait yedekleme geçmişini getir"""
        self.cursor.execute('''
            SELECT * FROM backup_history 
            WHERE project_id = ?
            ORDER BY backup_date DESC
        ''', (project_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_backup_details(self, backup_id: int) -> List[Dict]:
        """Yedekleme detaylarını getir"""
        self.cursor.execute('''
            SELECT bd.*, m.source_path, m.target_path
            FROM backup_details bd
            JOIN mappings m ON bd.mapping_id = m.id
            WHERE bd.backup_id = ?
        ''', (backup_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def delete_backup_history(self, backup_id: int):
        """Yedekleme geçmişini sil (cascade ile detaylar da silinir)"""
        self.cursor.execute('DELETE FROM backup_history WHERE id = ?', (backup_id,))
        self.conn.commit()
    
    # ==================== YEDEKLEME DOSYA DETAYLARI İŞLEMLERİ ====================
    
    def get_previous_file_size(self, file_path: str, file_name: str, current_backup_id: int) -> Optional[int]:
        """Dosyanın önceki yedeklemelerdeki boyutunu bul
        
        Args:
            file_path: Dosyanın dizin yolu
            file_name: Dosya adı
            current_backup_id: Mevcut yedekleme ID'si (bu ID'den öncekiler aranır)
        
        Returns:
            Önceki boyut (bytes) veya bulunamazsa None
        """
        self.cursor.execute('''
            SELECT file_size FROM backup_file_details
            WHERE file_path = ? AND file_name = ? AND backup_id < ?
            ORDER BY backup_id DESC
            LIMIT 1
        ''', (file_path, file_name, current_backup_id))
        row = self.cursor.fetchone()
        return row['file_size'] if row else None
    
    def add_backup_file_details(self, backup_id: int, file_details: List[Dict]):
        """Yedekleme dosya detaylarını toplu ekle
        
        Args:
            backup_id: Yedekleme ID'si
            file_details: Liste of dict, her biri şu anahtarları içerir:
                - mapping_id: Eşleşme ID'si (opsiyonel)
                - file_path: Dosyanın tam yolu
                - file_name: Dosya adı
                - file_size: Dosya boyutu (bytes)
                - previous_size: Önceki yedekleme boyutu (opsiyonel)
                - backup_reason: Yedekleme sebebi
        """
        for detail in file_details:
            mapping_id = detail.get('mapping_id')
            previous_size = detail.get('previous_size')
            self.cursor.execute('''
                INSERT INTO backup_file_details
                (backup_id, mapping_id, file_path, file_name, file_size, previous_size, backup_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (backup_id, mapping_id, detail['file_path'], detail['file_name'], 
                  detail['file_size'], previous_size, detail['backup_reason']))
        self.conn.commit()
    
    def _has_mapping_id_column(self) -> bool:
        """mapping_id kolonu var mı kontrol et"""
        try:
            self.cursor.execute("SELECT mapping_id FROM backup_file_details LIMIT 1")
            return True
        except sqlite3.OperationalError:
            return False
    
    def get_backup_file_details(self, backup_id: int) -> List[Dict]:
        """Yedekleme dosya detaylarını getir"""
        # mapping_id kolonu var mı kontrol et
        if self._has_mapping_id_column():
            self.cursor.execute('''
                SELECT * FROM backup_file_details
                WHERE backup_id = ?
                ORDER BY COALESCE(mapping_id, 0), file_path
            ''', (backup_id,))
        else:
            # Eski veritabanları için - mapping_id olmadan
            self.cursor.execute('''
                SELECT * FROM backup_file_details
                WHERE backup_id = ?
                ORDER BY file_path
            ''', (backup_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def has_backup_file_details(self, backup_id: int) -> bool:
        """Yedeklemenin dosya detayları var mı kontrol et"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM backup_file_details WHERE backup_id = ?
        ''', (backup_id,))
        return self.cursor.fetchone()[0] > 0
    
    # ==================== AYARLAR İŞLEMLERİ ====================
    
    def get_setting(self, key: str, default: str = "") -> str:
        """Ayar değeri getir"""
        self.cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = self.cursor.fetchone()
        return row['value'] if row else default
    
    def set_setting(self, key: str, value: str):
        """Ayar değeri kaydet"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))
        self.conn.commit()
    
    # ==================== ANALİZ SEÇİMLERİ İŞLEMLERİ ====================
    
    def get_analysis_selections(self, project_id: int) -> Dict:
        """Proje için kayıtlı analiz seçimlerini getir
        
        Returns:
            {
                'mapping_ids': [int, ...],
                'show_backup_files': bool,
                'show_user_excluded_files': bool,
                'show_hidden_excluded_files': bool,
                'show_skipped_files': bool,
                'show_revision_files': bool,
                'max_files_to_show': int
            }
        """
        self.cursor.execute(
            '''SELECT mapping_ids, show_backup_files, show_user_excluded_files,
                      show_hidden_excluded_files, show_skipped_files, 
                      show_revision_files, show_deleted_files, max_files_to_show 
               FROM analysis_selections WHERE project_id = ?''',
            (project_id,)
        )
        row = self.cursor.fetchone()
        if row:
            mapping_ids = []
            if row['mapping_ids']:
                # Comma-separated string'i integer listesine çevir
                mapping_ids = [int(mid) for mid in row['mapping_ids'].split(',') if mid.strip()]
            
            return {
                'mapping_ids': mapping_ids,
                'show_backup_files': bool(row['show_backup_files']),
                'show_user_excluded_files': bool(row['show_user_excluded_files']),
                'show_hidden_excluded_files': bool(row['show_hidden_excluded_files']),
                'show_skipped_files': bool(row['show_skipped_files']),
                'show_revision_files': bool(row['show_revision_files']),
                'show_deleted_files': bool(row['show_deleted_files']),
                'max_files_to_show': row['max_files_to_show'] or 50
            }
        
        # Varsayılan değerler
        return {
            'mapping_ids': [],
            'show_backup_files': True,
            'show_user_excluded_files': True,
            'show_hidden_excluded_files': True,
            'show_skipped_files': True,
            'show_revision_files': True,
            'show_deleted_files': True,
            'max_files_to_show': 50
        }
    
    def set_analysis_selections(self, project_id: int, mapping_ids: List[int],
                               show_backup_files: bool = True,
                               show_user_excluded_files: bool = True,
                               show_hidden_excluded_files: bool = True,
                               show_skipped_files: bool = True,
                               show_revision_files: bool = True,
                               show_deleted_files: bool = True,
                               max_files_to_show: int = 50):
        """Proje için analiz seçimlerini kaydet"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Integer listesini comma-separated string'e çevir
        mapping_ids_str = ','.join(str(mid) for mid in mapping_ids)
        self.cursor.execute('''
            INSERT OR REPLACE INTO analysis_selections 
            (project_id, mapping_ids, show_backup_files, show_user_excluded_files,
             show_hidden_excluded_files, show_skipped_files, show_revision_files, 
             show_deleted_files, max_files_to_show, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (project_id, mapping_ids_str, int(show_backup_files), int(show_user_excluded_files),
              int(show_hidden_excluded_files), int(show_skipped_files), 
              int(show_revision_files), int(show_deleted_files), max_files_to_show, now))
        self.conn.commit()
    
    def close(self):
        """Veritabanı bağlantısını kapat"""
        if self.conn:
            self.conn.close()
