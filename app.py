import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import csv
import os
from datetime import datetime

from database import Database
from reports import ReportGenerator
from forms import CountryParticipantsForm

class OlympicsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление Олимпийскими играми")
        self.root.geometry("1200x700")
        
        # Инициализация базы данных
        self.db = Database(
            host='192.168.56.101',  # Измените на ваш IP
            database='postgres',
            user='postgres',
            password='123456',    # Измените на ваш пароль
            port=5432
        )
        
        if not self.db.connect():
            self.root.destroy()
            return
        
        self.report_generator = ReportGenerator(self.db)
        
        # Список таблиц
        self.tables = [
            'countries',
            'sports', 
            'venues',
            'participants',
            'schedule',
            'results'
        ]
        
        self.table_names = {
            'countries': 'Страны',
            'sports': 'Виды спорта',
            'venues': 'Спортивные площадки',
            'participants': 'Участники',
            'schedule': 'Расписание стартов',
            'results': 'Результаты'
        }
        
        self.current_table = None
        self.current_data = []
        self.current_columns = []
        
        self.create_widgets()
        self.load_table_list()
        
        # Бинд закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Создание интерфейса приложения"""
        style = ttk.Style()
        style.configure("Treeview", 
                    rowheight=25,  # Высота строк
                    font=('Arial', 10))
        style.configure("Treeview.Heading",
                    font=('Arial', 10, 'bold'))
        # Главное меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Экспорт данных", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_closing)
        
        # Меню Отчеты
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Отчеты", menu=reports_menu)
        reports_menu.add_command(label="Медальный зачет", command=self.show_medals_report)
        reports_menu.add_command(label="Результаты спортсменов", command=self.show_results_report)
        reports_menu.add_command(label="Статистика по возрастам", command=self.show_age_report)
        reports_menu.add_command(label="Расписание на дату", command=self.show_schedule_report)
        
        # Меню Формы
        forms_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Формы", menu=forms_menu)
        forms_menu.add_command(label="Страна и участники", command=self.show_country_form)
        
        # Основной интерфейс
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Левая панель - управление таблицами
        left_panel = ttk.LabelFrame(main_frame, text="Таблицы", padding="10")
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Список таблиц
        ttk.Label(left_panel, text="Выберите таблицу:").grid(row=0, column=0, sticky=tk.W)
        self.table_listbox = tk.Listbox(left_panel, height=10, width=20)
        self.table_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 10))
        self.table_listbox.bind('<<ListboxSelect>>', self.on_table_select)
        
        # Кнопки управления таблицей
        ttk.Button(left_panel, text="Обновить", command=self.refresh_table).grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Button(left_panel, text="Добавить запись", command=self.show_add_form).grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Button(left_panel, text="Редактировать", command=self.show_edit_form).grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Button(left_panel, text="Удалить", command=self.delete_record).grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        # Поиск
        ttk.Label(left_panel, text="Поиск:").grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        self.search_field_var = tk.StringVar()
        self.search_field_combo = ttk.Combobox(left_panel, textvariable=self.search_field_var, width=18)
        self.search_field_combo.grid(row=7, column=0, sticky=tk.W, pady=(0, 5))
        
        self.search_value_var = tk.StringVar()
        ttk.Entry(left_panel, textvariable=self.search_value_var, width=20).grid(row=8, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Button(left_panel, text="Найти", command=self.search_records).grid(row=9, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Button(left_panel, text="Сбросить поиск", command=self.reset_search).grid(row=10, column=0, sticky=tk.W, pady=(0, 5))
        
        # Фильтры и сортировка
        ttk.Label(left_panel, text="Сортировка:").grid(row=11, column=0, sticky=tk.W, pady=(10, 5))
        self.sort_field_var = tk.StringVar()
        self.sort_field_combo = ttk.Combobox(left_panel, textvariable=self.sort_field_var, width=18)
        self.sort_field_combo.grid(row=12, column=0, sticky=tk.W, pady=(0, 5))
        
        self.sort_order_var = tk.StringVar(value="ASC")
        ttk.Radiobutton(left_panel, text="По возрастанию", variable=self.sort_order_var, value="ASC").grid(row=13, column=0, sticky=tk.W)
        ttk.Radiobutton(left_panel, text="По убыванию", variable=self.sort_order_var, value="DESC").grid(row=14, column=0, sticky=tk.W)
        ttk.Button(left_panel, text="Применить сортировку", command=self.apply_sort).grid(row=15, column=0, sticky=tk.W, pady=(5, 10))
        
        # Правая панель - отображение данных
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок таблицы
        self.table_title = ttk.Label(right_panel, text="Выберите таблицу", font=('Arial', 12, 'bold'))
        self.table_title.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Treeview для отображения данных
        self.tree = ttk.Treeview(right_panel, show='headings')
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Скроллбары
        vsb = ttk.Scrollbar(right_panel, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(right_panel, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.grid(row=1, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Статус бар
        self.status_bar = ttk.Label(right_panel, text="Готово", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Настройка расширения
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        left_panel.rowconfigure(1, weight=1)
    
    def load_table_list(self):
        """Загрузка списка таблиц"""
        self.table_listbox.delete(0, tk.END)
        for table in self.tables:
            display_name = self.table_names.get(table, table)
            self.table_listbox.insert(tk.END, display_name)
    
    def on_table_select(self, event):
        """Обработка выбора таблицы"""
        selection = self.table_listbox.curselection()
        if not selection:
            return
        
        table_display = self.table_listbox.get(selection[0])
        # Находим ключ таблицы по отображаемому имени
        for key, value in self.table_names.items():
            if value == table_display:
                self.current_table = key
                break
        self.sort_field_var.set('')
        
        self.load_table_data()
        self.load_table_fields()
    
    def load_table_data(self, filters=None):
        """Загрузка данных выбранной таблицы"""
        if not self.current_table:
            return
        
        try:
            self.table_title.config(text=f"Таблица: {self.table_names.get(self.current_table, self.current_table)}")
            
            # Получаем данные
            result, columns = self.db.get_table_data(
                self.current_table, 
                filters=filters,
                sort_field=self.sort_field_var.get() if self.sort_field_var.get() else None,
                sort_order=self.sort_order_var.get()
            )
            
            self.current_data = result
            self.current_columns = columns
            
            # Очищаем treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Настраиваем колонки
            self.tree["columns"] = columns
            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100, minwidth=50)
            
            # Заполняем данными
            for row in result:
                values = [row[col] if row[col] is not None else '' for col in columns]
                self.tree.insert("", tk.END, values=values)
            self.auto_size_columns()
            self.tree.update_idletasks()
            self.status_bar.config(text=f"Загружено записей: {len(result)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных:\n{str(e)}")
    
    def load_table_fields(self):
        """Загрузка полей таблицы для поиска и сортировки"""
        if not self.current_table:
            return
        
        try:
            result, _ = self.db.get_table_structure(self.current_table)
            fields = [row['column_name'] for row in result]
            
            # Обновляем комбобоксы
            self.search_field_combo['values'] = fields
            self.sort_field_combo['values'] = fields
            
            if fields:
                self.search_field_combo.set(fields[0])
                self.sort_field_combo.set(fields[0])
        
        except Exception as e:
            print(f"Ошибка при загрузке полей: {e}")
    
    def refresh_table(self):
        """Обновление данных таблицы"""
        self.load_table_data()
        
    
    
    def show_add_form(self):
        """Показать форму добавления записи"""
        if not self.current_table:
            messagebox.showwarning("Внимание", "Сначала выберите таблицу")
            return
        
        self.show_record_form(mode='add')
    
    def show_edit_form(self):
        """Показать форму редактирования записи"""
        if not self.current_table:
            messagebox.showwarning("Внимание", "Сначала выберите таблицу")
            return
        
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для редактирования")
            return
        
        self.show_record_form(mode='edit', selected_item=selected[0])
    
    def show_record_form(self, mode='add', selected_item=None):
        """Отображение формы для добавления/редактирования записи"""
        form_window = tk.Toplevel(self.root)
        form_window.title(f"{'Добавление' if mode == 'add' else 'Редактирование'} записи")
        form_window.geometry("500x400")
        
        # Получаем структуру таблицы
        try:
            structure, _ = self.db.get_table_structure(self.current_table)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить структуру таблицы:\n{str(e)}")
            form_window.destroy()
            return
        
        # Если редактирование - получаем данные записи
        record_data = {}
        if mode == 'edit' and selected_item:
            item_values = self.tree.item(selected_item)['values']
            for i, col in enumerate(self.current_columns):
                if i < len(item_values):
                    record_data[col] = item_values[i]
        
        # Создаем виджеты для полей
        entries = {}
        for i, field in enumerate(structure):
            field_name = field['column_name']
            field_type = field['data_type']
            
            # Пропускаем auto-increment поля при добавлении
            if mode == 'add' and field_name.endswith('_id') and 'nextval' in str(field.get('column_default', '')):
                continue
            
            # Метка
            label = ttk.Label(form_window, text=f"{field_name} ({field_type}):")
            label.grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
            
            # Поле ввода
            if field_type in ('date', 'timestamp'):
                # Для дат используем специальный виджет
                entry = DateEntry(form_window, width=20, date_pattern='yyyy-mm-dd')
                if field_name in record_data and record_data[field_name]:
                    entry.set_date(record_data[field_name])
            elif 'boolean' in field_type:
                # Для булевых значений - чекбокс
                var = tk.BooleanVar(value=record_data.get(field_name, False) if record_data else False)
                entry = ttk.Checkbutton(form_window, variable=var)
                entries[field_name] = var
                entry.grid(row=i, column=1, sticky=tk.W, padx=10, pady=5)
                continue
            else:
                # Обычное текстовое поле
                entry = ttk.Entry(form_window, width=30)
                if field_name in record_data and record_data[field_name] is not None:
                    entry.insert(0, str(record_data[field_name]))
            
            entries[field_name] = entry
            entry.grid(row=i, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Кнопки
        def save_record():
            try:
                data = {}
                for field_name, widget in entries.items():
                    if isinstance(widget, tk.BooleanVar):
                        value = widget.get()
                    elif isinstance(widget, DateEntry):
                        value = widget.get_date().strftime('%Y-%m-%d')
                    else:
                        value = widget.get().strip()
                        if value == '':
                            value = None
                    
                    data[field_name] = value
                
                if mode == 'add':
                    self.db.insert_record(self.current_table, data)
                    messagebox.showinfo("Успех", "Запись добавлена")
                else:
                    # Находим поле первичного ключа (обычно заканчивается на _id или code)
                    id_field = None
                    for field in structure:
                        if field['column_name'].endswith(('_id', '_code', 'id', 'code')):
                            id_field = field['column_name']
                            break
                    
                    if id_field and id_field in record_data:
                        self.db.update_record(self.current_table, record_data[id_field], data, id_field)
                        messagebox.showinfo("Успех", "Запись обновлена")
                    else:
                        messagebox.showerror("Ошибка", "Не найден идентификатор записи")
                
                self.load_table_data()
                form_window.destroy()
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении:\n{str(e)}")
        
        ttk.Button(form_window, text="Сохранить", command=save_record).grid(
            row=len(structure), column=0, padx=10, pady=20)
        ttk.Button(form_window, text="Отмена", command=form_window.destroy).grid(
            row=len(structure), column=1, padx=10, pady=20)
    
    def delete_record(self):
        """Удаление выбранной записи"""
        if not self.current_table:
            messagebox.showwarning("Внимание", "Сначала выберите таблицу")
            return
        
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return
        
        # Получаем значения выбранной строки
        item = self.tree.item(selected[0])
        values = item['values']
        
        # Создаем сообщение с данными записи
        record_info = "\n".join([f"{col}: {val}" for col, val in zip(self.current_columns[:5], values[:5])])
        
        if messagebox.askyesno("Подтверждение", f"Удалить запись?\n\n{record_info}"):
            try:
                # Находим первичный ключ (предполагаем, что это первый столбец)
                id_value = values[0]
                id_field = self.current_columns[0]
                
                self.db.delete_record(self.current_table, id_value, id_field)
                self.load_table_data()
                messagebox.showinfo("Успех", "Запись удалена")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении:\n{str(e)}")
    
    def search_records(self):
        """Поиск записей"""
        if not self.current_table:
            messagebox.showwarning("Внимание", "Сначала выберите таблицу")
            return
        
        field = self.search_field_var.get()
        value = self.search_value_var.get()
        
        if not field or not value:
            messagebox.showwarning("Внимание", "Заполните поле поиска")
            return
        
        try:
            result, columns = self.db.search_records(self.current_table, field, value)
            
            # Очищаем treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Заполняем результатами поиска
            for row in result:
                values = [row[col] if row[col] is not None else '' for col in columns]
                self.tree.insert("", tk.END, values=values)
            
            self.status_bar.config(text=f"Найдено записей: {len(result)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при поиске:\n{str(e)}")
    
    def reset_search(self):
        """Сброс поиска"""
        self.search_value_var.set('')
        self.load_table_data()
    
    def apply_sort(self):
        """Применение сортировки"""
        if self.current_table:
            self.load_table_data()
    
    def show_medals_report(self):
        """Отчет: медальный зачет"""
        self.show_report_dialog('medals')
    
    def show_results_report(self):
        """Отчет: результаты спортсменов"""
        self.show_report_dialog('results')
    
    def show_age_report(self):
        """Отчет: статистика по возрастам"""
        self.show_report_dialog('age')
    
    def show_schedule_report(self):
        """Отчет: расписание на дату"""
        # Специальный диалог для выбора даты
        dialog = tk.Toplevel(self.root)
        dialog.title("Расписание на дату")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="Выберите дату:", font=('Arial', 10)).pack(pady=10)
        
        date_entry = DateEntry(dialog, width=20, date_pattern='yyyy-mm-dd')
        date_entry.pack(pady=10)
        
        def generate_report():
            date = date_entry.get_date().strftime('%Y-%m-%d')
            dialog.destroy()
            self.display_report('schedule', {'date': date})
        
        ttk.Button(dialog, text="Сформировать отчет", command=generate_report).pack(pady=20)
    
    def show_report_dialog(self, report_type):
        """Диалог выбора параметров отчета"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Параметры отчета: {report_type}")
        dialog.geometry("400x500")
        
        # Поля для фильтров
        filters = {}
        
        if report_type == 'medals':
            ttk.Label(dialog, text="Медальный зачет", font=('Arial', 12, 'bold')).pack(pady=10)
            
            # Страна
            ttk.Label(dialog, text="Страна:").pack(anchor=tk.W, padx=20, pady=(10, 0))
            country_var = tk.StringVar()
            ttk.Entry(dialog, textvariable=country_var, width=30).pack(padx=20, pady=(0, 10))
            filters['country_name'] = country_var
            
            # Континент
            ttk.Label(dialog, text="Континент:").pack(anchor=tk.W, padx=20)
            continent_var = tk.StringVar()
            ttk.Combobox(dialog, textvariable=continent_var, 
                        values=['', 'Азия', 'Европа', 'Африка', 'Северная Америка', 
                                'Южная Америка', 'Австралия'], width=20).pack(padx=20, pady=(0, 10))
            filters['continent'] = continent_var
            
            # Минимальное количество медалей
            ttk.Label(dialog, text="Минимум медалей:").pack(anchor=tk.W, padx=20)
            min_medals_var = tk.StringVar()
            ttk.Entry(dialog, textvariable=min_medals_var, width=10).pack(padx=20, pady=(0, 10))
            filters['min_medals'] = min_medals_var
            
        elif report_type == 'results':
            ttk.Label(dialog, text="Результаты спортсменов", font=('Arial', 12, 'bold')).pack(pady=10)
            
            # Страна
            ttk.Label(dialog, text="Страна:").pack(anchor=tk.W, padx=20, pady=(10, 0))
            country_var = tk.StringVar()
            ttk.Entry(dialog, textvariable=country_var, width=30).pack(padx=20, pady=(0, 10))
            filters['country_name'] = country_var
            
            # Вид спорта
            ttk.Label(dialog, text="Вид спорта:").pack(anchor=tk.W, padx=20)
            sport_var = tk.StringVar()
            ttk.Entry(dialog, textvariable=sport_var, width=30).pack(padx=20, pady=(0, 10))
            filters['sport_name'] = sport_var
            
            # Медаль
            ttk.Label(dialog, text="Медаль:").pack(anchor=tk.W, padx=20)
            medal_var = tk.StringVar()
            ttk.Combobox(dialog, textvariable=medal_var, 
                        values=['', 'золото', 'серебро', 'бронза'], width=15).pack(padx=20, pady=(0, 10))
            filters['medal'] = medal_var
        
        elif report_type == 'age':
            ttk.Label(dialog, text="Статистика по возрастам", font=('Arial', 12, 'bold')).pack(pady=10)
            
            # Страна
            ttk.Label(dialog, text="Страна:").pack(anchor=tk.W, padx=20, pady=(10, 0))
            country_var = tk.StringVar()
            ttk.Entry(dialog, textvariable=country_var, width=30).pack(padx=20, pady=(0, 10))
            filters['country_name'] = country_var
            
            # Вид спорта
            ttk.Label(dialog, text="Вид спорта:").pack(anchor=tk.W, padx=20)
            sport_var = tk.StringVar()
            ttk.Entry(dialog, textvariable=sport_var, width=30).pack(padx=20, pady=(0, 10))
            filters['sport_name'] = sport_var
            
            # Командный/индивидуальный
            ttk.Label(dialog, text="Тип спорта:").pack(anchor=tk.W, padx=20)
            is_team_var = tk.StringVar()
            ttk.Combobox(dialog, textvariable=is_team_var, 
                        values=['', 'да', 'нет'], width=10).pack(padx=20, pady=(0, 10))
            filters['is_team'] = is_team_var
        
        # Сортировка
        ttk.Label(dialog, text="Сортировка:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        sort_var = tk.StringVar()
        sort_combo = ttk.Combobox(dialog, textvariable=sort_var, width=30)
        sort_combo.pack(padx=20, pady=(0, 20))
        
        # Заполняем варианты сортировки в зависимости от отчета
        if report_type == 'medals':
            sort_combo['values'] = [
                'gold_medals DESC, silver_medals DESC, bronze_medals DESC',
                'total_medals DESC',
                'medal_points DESC',
                'country_name ASC'
            ]
        elif report_type == 'results':
            sort_combo['values'] = [
                'position ASC',
                'country_name ASC, sport_name ASC',
                'full_name ASC',
                'age DESC'
            ]
        elif report_type == 'age':
            sort_combo['values'] = [
                'avg_age DESC',
                'participants_count DESC',
                'country_name ASC, sport_name ASC'
            ]
        
        sort_combo.current(0)
        
        def generate_report():
            # Собираем фильтры
            report_filters = {}
            for key, var in filters.items():
                value = var.get().strip()
                if value:
                    report_filters[key] = value
            
            sort_by = sort_var.get() if sort_var.get() else None
            
            dialog.destroy()
            self.display_report(report_type, report_filters, sort_by)
        
        ttk.Button(dialog, text="Сформировать отчет", command=generate_report).pack(pady=20)
    
    def display_report(self, report_type, filters=None, sort_by=None):
        """Отображение отчета в новом окне"""
        try:
            if report_type == 'medals':
                result, columns = self.report_generator.generate_medals_by_country(filters, sort_by)
                title = "Медальный зачет стран"
            elif report_type == 'results':
                result, columns = self.report_generator.generate_participants_results(filters, sort_by)
                title = "Результаты спортсменов"
            elif report_type == 'age':
                result, columns = self.report_generator.generate_age_statistics(filters, sort_by)
                title = "Статистика по возрастам"
            elif report_type == 'schedule':
                result, columns = self.report_generator.generate_daily_schedule(filters['date'])
                title = f"Расписание на {filters['date']}"
            else:
                return
            
            # Создаем окно отчета
            report_window = tk.Toplevel(self.root)
            report_window.title(title)
            report_window.geometry("1000x600")
            
            # Заголовок
            ttk.Label(report_window, text=title, font=('Arial', 14, 'bold')).pack(pady=10)
            
            # Treeview для отображения отчета
            tree = ttk.Treeview(report_window, show='headings')
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Настраиваем колонки
            tree["columns"] = columns
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100, minwidth=50)
            
            # Заполняем данными
            for row in result:
                values = [row[col] if row[col] is not None else '' for col in columns]
                tree.insert("", tk.END, values=values)
            
            # Скроллбары
            vsb = ttk.Scrollbar(report_window, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(report_window, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            
            vsb.pack(side=tk.RIGHT, fill=tk.Y)
            hsb.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Статистика
            ttk.Label(report_window, 
                     text=f"Всего записей: {len(result)} | Фильтры: {filters if filters else 'нет'}").pack(pady=5)
            
            # Кнопка экспорта
            def export_report():
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    initialfile=f"{report_type}_report.csv"
                )
                if filename:
                    self.export_to_csv(result, columns, filename)
            
            ttk.Button(report_window, text="Экспорт в CSV", command=export_report).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при формировании отчета:\n{str(e)}")
    
    def show_country_form(self):
        """Показать форму для работы со страной и участниками"""
        form_window = tk.Toplevel(self.root)
        form_window.title("Страна и участники")
        form_window.geometry("800x600")
        
        CountryParticipantsForm(form_window, self.db)
    
    def export_data(self):
        """Экспорт данных текущей таблицы"""
        if not self.current_table or not self.current_data:
            messagebox.showwarning("Внимание", "Нет данных для экспорта")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{self.current_table}.csv"
        )
        
        if filename:
            self.export_to_csv(self.current_data, self.current_columns, filename)
    
    def export_to_csv(self, data, columns, filename):
        """Экспорт данных в CSV файл"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Заголовки
                writer.writerow(columns)
                
                # Данные
                for row in data:
                    writer.writerow([row[col] for col in columns])
            
            messagebox.showinfo("Успех", f"Данные экспортированы в {filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте:\n{str(e)}")
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.db.disconnect()
            self.root.destroy()
    def auto_size_columns(self):
        if not self.current_columns:
            return
    
        try:
            # Получаем информацию о типах данных столбцов
            structure, _ = self.db.get_table_structure(self.current_table)
            type_info = {row['column_name']: row['data_type'] for row in structure}
        except:
            type_info = {}
        
        for col in self.current_columns:
            data_type = type_info.get(col, '').lower()
            
            # Определяем базовую ширину по типу данных
            if any(num_type in data_type for num_type in ['int', 'numeric', 'decimal']):
                base_width = 70  # Числовые поля
            elif 'date' in data_type:
                base_width = 90  # Даты
            elif 'time' in data_type:
                base_width = 80  # Время
            elif 'bool' in data_type:
                base_width = 60  # Логические значения
            elif col.endswith('_id'):
                base_width = 60  # ID поля
            elif any(name in col.lower() for name in ['name', 'title', 'description']):
                base_width = 150  # Названия
            else:
                base_width = 100  # По умолчанию
            
            # Находим максимальную длину текста в столбце
            max_len = len(col)  # начинаем с длины заголовка
            
            for row in self.current_data:
                value = row.get(col, '')
                if value is not None:
                    text = str(value)
                    # Ограничиваем очень длинные тексты
                    if len(text) > 50:
                        text = text[:47] + "..."
                    if len(text) > max_len:
                        max_len = len(text)
            
            # Вычисляем ширину (примерно 8 пикселей на символ)
            col_width = min(max(base_width, max_len * 8), 300)
            
            # Особые настройки для веса и роста
            if col.lower() in ['weight', 'вес']:
                col_width = 80
            elif col.lower() in ['height', 'рост']:
                col_width = 80
            elif col.lower() in ['full_name', 'имя', 'фамилия']:
                col_width = 180
            
            self.tree.column(col, width=col_width, minwidth=base_width, stretch=False)
            
        # Принудительно обновляем отображение
        self.tree.update_idletasks()       
            


def main():
    """Точка входа в приложение"""
    root = tk.Tk()
    app = OlympicsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()