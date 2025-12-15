import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import Database

class CountryParticipantsForm:
    """Форма для работы со страной и её участниками (отношение 1:М)"""
    
    def __init__(self, parent, db: Database):
        self.parent = parent
        self.db = db
        self.current_country = None
        self.current_country_code = None
        
        self.create_widgets()
    
    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Раздел страны
        country_frame = ttk.LabelFrame(main_frame, text="Данные страны", padding="10")
        country_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Поля страны
        ttk.Label(country_frame, text="Код страны:").grid(row=0, column=0, sticky=tk.W)
        self.country_code_var = tk.StringVar()
        self.country_code_entry = ttk.Entry(country_frame, textvariable=self.country_code_var, width=10)
        self.country_code_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))
        
        ttk.Label(country_frame, text="Название:").grid(row=0, column=2, sticky=tk.W)
        self.country_name_var = tk.StringVar()
        self.country_name_entry = ttk.Entry(country_frame, textvariable=self.country_name_var, width=30)
        self.country_name_entry.grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(country_frame, text="Континент:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.continent_var = tk.StringVar()
        self.continent_combo = ttk.Combobox(country_frame, textvariable=self.continent_var, 
                                          values=['Азия', 'Европа', 'Африка', 'Северная Америка', 
                                                  'Южная Америка', 'Австралия'], width=20)
        self.continent_combo.grid(row=1, column=1, sticky=tk.W, padx=(5, 20), pady=(10, 0))
        
        # Кнопки управления страной
        btn_frame = ttk.Frame(country_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Найти страну", command=self.load_country).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Сохранить страну", command=self.save_country).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Новая страна", command=self.new_country).pack(side=tk.LEFT, padx=2)
        
        # Раздел участников
        participants_frame = ttk.LabelFrame(main_frame, text="Участники страны", padding="10")
        participants_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Таблица участников
        columns = ('ID', 'ФИО', 'Дата рождения', 'Пол', 'Вид спорта')
        self.participants_tree = ttk.Treeview(participants_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.participants_tree.heading(col, text=col)
            self.participants_tree.column(col, width=120)
        
        self.participants_tree.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Скроллбар для таблицы
        scrollbar = ttk.Scrollbar(participants_frame, orient=tk.VERTICAL, 
                                command=self.participants_tree.yview)
        self.participants_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        
        # Форма добавления/редактирования участника
        form_frame = ttk.Frame(participants_frame)
        form_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Поля участника
        ttk.Label(form_frame, text="ФИО:").grid(row=0, column=0, sticky=tk.W)
        self.participant_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.participant_name_var, width=40).grid(row=0, column=1, sticky=tk.W, padx=(5, 20))
        
        ttk.Label(form_frame, text="Дата рождения:").grid(row=0, column=2, sticky=tk.W)
        self.participant_birth_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.participant_birth_var, width=15).grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(form_frame, text="Пол:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.participant_gender_var = tk.StringVar()
        ttk.Combobox(form_frame, textvariable=self.participant_gender_var, 
                    values=['M', 'F'], width=5).grid(row=1, column=1, sticky=tk.W, padx=(5, 20), pady=(10, 0))
        
        ttk.Label(form_frame, text="Вид спорта:").grid(row=1, column=2, sticky=tk.W, pady=(10, 0))
        self.participant_sport_var = tk.StringVar()
        self.load_sports()
        ttk.Combobox(form_frame, textvariable=self.participant_sport_var, 
                    values=self.sports_list, width=15).grid(row=1, column=3, sticky=tk.W, pady=(10, 0))
        
        # Кнопки управления участниками
        btn_frame2 = ttk.Frame(participants_frame)
        btn_frame2.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(btn_frame2, text="Добавить участника", command=self.add_participant).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="Удалить участника", command=self.delete_participant).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="Обновить данные", command=self.refresh_participants).pack(side=tk.LEFT, padx=2)
    
    def load_sports(self):
        """Загрузка списка видов спорта"""
        try:
            result, _ = self.db.execute_query("SELECT sport_code, sport_name FROM sports ORDER BY sport_name")
            self.sports_list = [f"{row['sport_code']} - {row['sport_name']}" for row in result]
            self.sports_dict = {row['sport_code']: row['sport_name'] for row in result}
        except:
            self.sports_list = []
            self.sports_dict = {}
    
    def load_country(self):
        """Загрузка данных страны"""
        country_code = self.country_code_var.get().strip().upper()
        if not country_code:
            messagebox.showwarning("Внимание", "Введите код страны")
            return
        
        try:
            # Загружаем данные страны
            query = "SELECT * FROM countries WHERE country_code = %s"
            result, _ = self.db.execute_query(query, [country_code])
            
            if result:
                self.current_country = result[0]
                self.current_country_code = country_code
                
                # Заполняем поля
                self.country_name_var.set(self.current_country['country_name'])
                self.continent_var.set(self.current_country.get('continent', ''))
                
                # Загружаем участников
                self.load_country_participants()
                messagebox.showinfo("Успех", f"Загружена страна: {self.current_country['country_name']}")
            else:
                messagebox.showwarning("Внимание", f"Страна с кодом {country_code} не найдена")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке страны:\n{str(e)}")
    
    def load_country_participants(self):
        """Загрузка участников страны"""
        if not self.current_country_code:
            return
        
        # Очищаем таблицу
        for item in self.participants_tree.get_children():
            self.participants_tree.delete(item)
        
        try:
            query = """
            SELECT p.participant_id, p.full_name, p.birth_date, p.gender, s.sport_name
            FROM participants p
            JOIN sports s ON p.sport_code = s.sport_code
            WHERE p.country_code = %s
            ORDER BY p.full_name
            """
            result, _ = self.db.execute_query(query, [self.current_country_code])
            
            for row in result:
                self.participants_tree.insert('', tk.END, values=(
                    row['participant_id'],
                    row['full_name'],
                    row['birth_date'].strftime('%Y-%m-%d') if row['birth_date'] else '',
                    'Мужской' if row['gender'] == 'M' else 'Женский',
                    row['sport_name']
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке участников:\n{str(e)}")
    
    def save_country(self):
        """Сохранение данных страны"""
        if not self.current_country_code:
            messagebox.showwarning("Внимание", "Сначала загрузите или создайте страну")
            return
        
        country_data = {
            'country_code': self.current_country_code,
            'country_name': self.country_name_var.get().strip(),
            'continent': self.continent_var.get().strip()
        }
        
        if not all(country_data.values()):
            messagebox.showwarning("Внимание", "Заполните все поля страны")
            return
        
        try:
            if self.current_country:
                # Обновление существующей страны
                query = """
                UPDATE countries 
                SET country_name = %s, continent = %s
                WHERE country_code = %s
                """
                self.db.execute_query(query, [
                    country_data['country_name'],
                    country_data['continent'],
                    country_data['country_code']
                ], fetch=False)
            else:
                # Создание новой страны
                query = """
                INSERT INTO countries (country_code, country_name, continent)
                VALUES (%s, %s, %s)
                """
                self.db.execute_query(query, [
                    country_data['country_code'],
                    country_data['country_name'],
                    country_data['continent']
                ], fetch=False)
            
            messagebox.showinfo("Успех", "Данные страны сохранены")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении страны:\n{str(e)}")
    
    def new_country(self):
        """Создание новой страны"""
        self.current_country = None
        self.current_country_code = self.country_code_var.get().strip().upper()
        
        if not self.current_country_code:
            messagebox.showwarning("Внимание", "Введите код новой страны")
            return
        
        # Очищаем поля
        self.country_name_var.set('')
        self.continent_var.set('')
        
        # Очищаем таблицу участников
        for item in self.participants_tree.get_children():
            self.participants_tree.delete(item)
        
        messagebox.showinfo("Информация", f"Создание новой страны с кодом {self.current_country_code}")
    
    def add_participant(self):
        """Добавление нового участника"""
        if not self.current_country_code:
            messagebox.showwarning("Внимание", "Сначала загрузите или создайте страну")
            return
        
        # Получаем данные из формы
        full_name = self.participant_name_var.get().strip()
        birth_date = self.participant_birth_var.get().strip()
        gender = self.participant_gender_var.get().strip().upper()
        sport_info = self.participant_sport_var.get().strip()
        
        if not all([full_name, birth_date, gender, sport_info]):
            messagebox.showwarning("Внимание", "Заполните все поля участника")
            return
        
        # Извлекаем код спорта из комбобокса
        sport_code = sport_info.split(' - ')[0] if ' - ' in sport_info else sport_info
        
        try:
            # Проверяем валидность даты
            datetime.strptime(birth_date, '%Y-%m-%d')
            
            # Добавляем участника
            participant_data = {
                'country_code': self.current_country_code,
                'sport_code': sport_code,
                'full_name': full_name,
                'birth_date': birth_date,
                'gender': gender
            }
            
            self.db.insert_record('participants', participant_data)
            
            # Очищаем форму и обновляем список
            self.participant_name_var.set('')
            self.participant_birth_var.set('')
            self.participant_gender_var.set('')
            self.participant_sport_var.set('')
            
            self.load_country_participants()
            messagebox.showinfo("Успех", "Участник добавлен")
            
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении участника:\n{str(e)}")
    
    def delete_participant(self):
        """Удаление выбранного участника"""
        selected = self.participants_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите участника для удаления")
            return
        
        item = self.participants_tree.item(selected[0])
        participant_id = item['values'][0]
        participant_name = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить участника {participant_name}?"):
            try:
                self.db.delete_record('participants', participant_id, 'participant_id')
                self.load_country_participants()
                messagebox.showinfo("Успех", "Участник удален")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении участника:\n{str(e)}")
    
    def refresh_participants(self):
        """Обновление списка участников"""
        if self.current_country_code:
            self.load_country_participants()