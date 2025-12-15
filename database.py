import psycopg2
from psycopg2.extras import DictCursor
from typing import List, Dict, Any, Optional
import tkinter.messagebox as messagebox

class Database:
    def __init__(self, host='192.168.56.101', database='postgres', 
                 user='postgres', password='123456', port=5432):
        self.connection_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port
        }
        self.connection = None
        
    def connect(self):
        """Установка соединения с базой данных"""
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            return True
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к БД:\n{str(e)}")
            return False
    
    def disconnect(self):
        """Закрытие соединения"""
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params=None, fetch=True):
        """Выполнение SQL-запроса"""
        try:
            with self.connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, params or ())
                if fetch and cursor.description:
                    result = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    return result, columns
                elif not fetch:
                    self.connection.commit()
                    return cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            raise e
    
    def get_table_data(self, table_name: str, filters: Dict = None, 
                      sort_field: str = None, sort_order: str = 'ASC'):
        """Получение данных из таблицы с фильтрацией и сортировкой"""
        query = f"SELECT * FROM {table_name}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if value is not None:
                    conditions.append(f"{key} = %s")
                    params.append(value)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        if sort_field:
            query += f" ORDER BY {sort_field} {sort_order}"
        
        return self.execute_query(query, params)
    
    def insert_record(self, table_name: str, data: Dict):
        """Добавление новой записи"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return self.execute_query(query, list(data.values()), fetch=False)
    
    def update_record(self, table_name: str, record_id: int, data: Dict, id_field='id'):
        """Обновление записи"""
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {id_field} = %s"
        params = list(data.values()) + [record_id]
        return self.execute_query(query, params, fetch=False)
    
    def delete_record(self, table_name: str, record_id: int, id_field='id'):
        """Удаление записи"""
        query = f"DELETE FROM {table_name} WHERE {id_field} = %s"
        return self.execute_query(query, [record_id], fetch=False)
    
    def search_records(self, table_name: str, field: str, value: str):
        """Поиск записей по полю"""
        try:
            # Простое решение: преобразуем все в текст для поиска
            query = f"SELECT * FROM {table_name} WHERE {field}::TEXT ILIKE %s"
            return self.execute_query(query, [f'%{value}%'])
        except Exception as e:
            # Если не сработало, пробуем альтернативный подход
            try:
                # Пробуем точное совпадение
                query = f"SELECT * FROM {table_name} WHERE {field} = %s"
                return self.execute_query(query, [value])
            except:
                raise Exception(f"Ошибка поиска по полю '{field}': {str(e)}")
    
    def get_table_structure(self, table_name: str):
        """Получение структуры таблицы"""
        query = """
        SELECT 
            column_name, 
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = %s
        ORDER BY ordinal_position
        """
        return self.execute_query(query, [table_name])
    
    def get_foreign_keys(self, table_name: str):
        """Получение информации о внешних ключах"""
        query = """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = %s
        """
        return self.execute_query(query, [table_name])