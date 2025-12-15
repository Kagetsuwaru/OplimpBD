from database import Database
from typing import Dict, List, Any
from datetime import datetime

class ReportGenerator:
    def __init__(self, db: Database):
        self.db = db
    
    def generate_medals_by_country(self, filters: Dict = None, sort_by: str = None):
        """Отчет: страны с количеством медалей"""
        # Базовый запрос через CTE
        base_query = """
        WITH medal_counts AS (
            SELECT 
                c.country_code,
                c.country_name,
                c.continent,
                COUNT(CASE WHEN r.medal = 'золото' THEN 1 END) as gold_medals,
                COUNT(CASE WHEN r.medal = 'серебро' THEN 1 END) as silver_medals,
                COUNT(CASE WHEN r.medal = 'бронза' THEN 1 END) as bronze_medals,
                COUNT(r.medal) as total_medals,
                SUM(CASE 
                    WHEN r.medal = 'золото' THEN 3 
                    WHEN r.medal = 'серебро' THEN 2 
                    WHEN r.medal = 'бронза' THEN 1 
                    ELSE 0 
                END) as medal_points
            FROM countries c
            LEFT JOIN participants p ON c.country_code = p.country_code
            LEFT JOIN results r ON p.participant_id = r.participant_id AND r.medal IS NOT NULL
            WHERE 1=1
        """
        
        where_conditions = []
        params = []
        
        if filters:
            if filters.get('country_name'):
                where_conditions.append("c.country_name ILIKE %s")
                params.append(f"%{filters['country_name']}%")
            if filters.get('continent'):
                where_conditions.append("c.continent = %s")
                params.append(filters['continent'])
        
        if where_conditions:
            base_query += " AND " + " AND ".join(where_conditions)
        
        base_query += " GROUP BY c.country_code, c.country_name, c.continent )"
        
        base_query += " SELECT * FROM medal_counts WHERE 1=1"
        
        if filters and filters.get('min_medals'):
            base_query += " AND total_medals >= %s"
            params.append(int(filters['min_medals']))
        
        if sort_by:
            base_query += f" ORDER BY {sort_by}"
        else:
            base_query += " ORDER BY gold_medals DESC, silver_medals DESC, bronze_medals DESC"
        
        return self.db.execute_query(base_query, params)
    
    def generate_participants_results(self, filters: Dict = None, sort_by: str = None):
        """Отчет: результаты спортсменов"""
        query = """
        SELECT 
            p.participant_id,
            p.full_name,
            EXTRACT(YEAR FROM AGE(p.birth_date)) as age,
            c.country_name,
            s.sport_name,
            s.is_team,
            sch.start_date,
            sch.stage,
            r.position,
            r.medal,
            r.result_value,
            CASE 
                WHEN r.position = 1 THEN 'Победитель'
                WHEN r.position <= 3 THEN 'Призер'
                ELSE 'Участник'
            END as result_category
        FROM results r
        JOIN participants p ON r.participant_id = p.participant_id
        JOIN countries c ON p.country_code = c.country_code
        JOIN sports s ON p.sport_code = s.sport_code
        JOIN schedule sch ON r.schedule_id = sch.schedule_id
        """
        
        where_conditions = []
        params = []
        
        if filters:
            if filters.get('country_name'):
                where_conditions.append("c.country_name ILIKE %s")
                params.append(f"%{filters['country_name']}%")
            if filters.get('sport_name'):
                where_conditions.append("s.sport_name ILIKE %s")
                params.append(f"%{filters['sport_name']}%")
            if filters.get('medal'):
                where_conditions.append("r.medal = %s")
                params.append(filters['medal'])
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        if sort_by:
            query += f" ORDER BY {sort_by}"
        else:
            query += " ORDER BY c.country_name, s.sport_name, r.position"
        
        return self.db.execute_query(query, params)
    
    def generate_age_statistics(self, filters: Dict = None, sort_by: str = None):
        """Отчет: статистика по возрастам"""
        query = """
        SELECT 
            c.country_name,
            s.sport_name,
            s.is_team,
            COUNT(*) as participants_count,
            ROUND(AVG(EXTRACT(YEAR FROM AGE(p.birth_date)))::numeric, 1) as avg_age,
            MIN(EXTRACT(YEAR FROM AGE(p.birth_date))) as min_age,
            MAX(EXTRACT(YEAR FROM AGE(p.birth_date))) as max_age,
            COUNT(CASE WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) < 20 THEN 1 END) as under_20,
            COUNT(CASE WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 20 AND 25 THEN 1 END) as age_20_25,
            COUNT(CASE WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) > 25 THEN 1 END) as over_25
        FROM participants p
        JOIN countries c ON p.country_code = c.country_code
        JOIN sports s ON p.sport_code = s.sport_code
        """
        
        where_conditions = []
        params = []
        
        if filters:
            if filters.get('country_name'):
                where_conditions.append("c.country_name ILIKE %s")
                params.append(f"%{filters['country_name']}%")
            if filters.get('sport_name'):
                where_conditions.append("s.sport_name ILIKE %s")
                params.append(f"%{filters['sport_name']}%")
            if filters.get('is_team'):
                where_conditions.append("s.is_team = %s")
                params.append(filters['is_team'] == 'да')
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += """
        GROUP BY c.country_name, s.sport_name, s.is_team
        HAVING COUNT(*) >= 1
        """
        
        if sort_by:
            query += f" ORDER BY {sort_by}"
        else:
            query += " ORDER BY avg_age DESC, participants_count DESC"
        
        return self.db.execute_query(query, params)
    
    def generate_daily_schedule(self, date: str):
        """Отчет: расписание стартов на заданную дату"""
        query = """
        SELECT 
            s.schedule_id,
            s.start_date,
            s.start_time,
            v.venue_name,
            v.location,
            sp.sport_name,
            s.stage,
            s.status,
            COUNT(DISTINCT r.participant_id) as participants_count
        FROM schedule s
        JOIN venues v ON s.venue_code = v.venue_code
        JOIN sports sp ON s.sport_code = sp.sport_code
        LEFT JOIN results r ON s.schedule_id = r.schedule_id
        WHERE s.start_date = %s
        GROUP BY s.schedule_id, s.start_date, s.start_time, v.venue_name, 
                 v.location, sp.sport_name, s.stage, s.status
        ORDER BY s.start_time, v.venue_name
        """
        
        return self.db.execute_query(query, [date])