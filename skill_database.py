"""
skill_database.py
Полная база данных скиллов и баффов для Perfect World Asgard
Содержит классы для работы со скиллами и баффами, загрузку из JSON
"""

import json
import csv
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class SkillClass(Enum):
    """Классы персонажей в Perfect World"""
    WARRIOR = "воин"
    MAGE = "маг"
    PRIEST = "жрец"
    ASSASSIN = "убийца"
    BARBARIAN = "варвар"
    VENOMANCER = "venomancer"
    ARCHER = "лучник"
    MYSTIC = "мистик"
    UNKNOWN = "неизвестно"


class ElementType(Enum):
    """Типы стихий"""
    FIRE = "огонь"
    WATER = "вода"
    EARTH = "земля"
    WIND = "ветер"
    WOOD = "дерево"
    METAL = "металл"
    DARK = "тьма"
    LIGHT = "свет"
    PHYSICAL = "физический"
    NEUTRAL = "нейтральный"


@dataclass
class Buff:
    """
    Класс, представляющий бафф (временный эффект), влияющий на скорость каста.
    """
    id: int = 0
    name: str = ""
    duration: float = 0.0          # длительность в секундах
    channeling_bonus: int = 0       # процент увеличения скорости каста (например, 20)
    description: str = ""
    icon: str = ""
    skill_class: Optional[SkillClass] = None  # для каких классов доступен, если None – для всех

    def __post_init__(self):
        if isinstance(self.skill_class, str):
            try:
                self.skill_class = SkillClass(self.skill_class)
            except ValueError:
                self.skill_class = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
            "duration": self.duration,
            "channeling_bonus": self.channeling_bonus,
            "description": self.description,
            "icon": self.icon
        }
        if self.skill_class:
            result["class"] = self.skill_class.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Buff':
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            duration=data.get("duration", 0.0),
            channeling_bonus=data.get("channeling_bonus", 0),
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            skill_class=data.get("class")
        )


@dataclass
class Skill:
    """
    Класс, представляющий скилл в Perfect World
    Содержит все параметры, включая те, что есть в image.png
    """
    # Основные параметры
    id: int = 0
    name: str = ""
    level: int = 1
    skill_class: SkillClass = SkillClass.UNKNOWN
    
    # Параметры из скриншота
    range: float = 0.0  # Дальность в метрах
    magic_cost: int = 0  # Маг. энергия / Мар. энергия
    cast_time: float = 0.0  # Подготовка в секундах
    apply_time: float = 0.0  # Применение в секундах
    cooldown: float = 0.0  # Перезарядка в секундах
    chi_gain: float = 0.0  # Получение ци
    
    # Ограничения
    weapon_restriction: List[str] = field(default_factory=list)  # Ограничение по оружию
    
    # Эффекты и урон
    description: str = ""  # Полное описание
    status: str = ""  # Статус (например "Демон")
    base_damage: int = 0  # Базовый магический урон
    weapon_damage_percent: int = 0  # Процент урона оружия
    element_damage: Dict[ElementType, int] = field(default_factory=dict)  # Урон стихиями
    
    # Дополнительные параметры
    target_type: str = "enemy"  # enemy, self, party, area
    area_size: float = 0.0  # Размер зоны поражения
    push_back: float = 0.0  # Отталкивание в метрах
    duration: float = 0.0  # Длительность эффекта
    
    # Визуальные данные
    icon: str = ""  # Путь к иконке
    
    def __post_init__(self):
        """Обработка после инициализации"""
        if isinstance(self.skill_class, str):
            try:
                self.skill_class = SkillClass(self.skill_class)
            except ValueError:
                self.skill_class = SkillClass.UNKNOWN
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для JSON"""
        result = {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "class": self.skill_class.value if isinstance(self.skill_class, SkillClass) else self.skill_class,
            "range": self.range,
            "magic_cost": self.magic_cost,
            "cast_time": self.cast_time,
            "apply_time": self.apply_time,
            "cooldown": self.cooldown,
            "chi_gain": self.chi_gain,
            "weapon_restriction": self.weapon_restriction,
            "description": self.description,
            "status": self.status,
            "base_damage": self.base_damage,
            "weapon_damage_percent": self.weapon_damage_percent,
            "element_damage": {k.value if isinstance(k, ElementType) else k: v 
                              for k, v in self.element_damage.items()},
            "target_type": self.target_type,
            "area_size": self.area_size,
            "push_back": self.push_back,
            "duration": self.duration,
            "icon": self.icon
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Skill':
        """Создание из словаря"""
        # Обработка element_damage
        element_damage = {}
        if "element_damage" in data:
            for k, v in data["element_damage"].items():
                try:
                    element_key = ElementType(k)
                except ValueError:
                    element_key = k
                element_damage[element_key] = v
        
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            level=data.get("level", 1),
            skill_class=data.get("class", "неизвестно"),
            range=data.get("range", 0.0),
            magic_cost=data.get("magic_cost", 0),
            cast_time=data.get("cast_time", 0.0),
            apply_time=data.get("apply_time", 0.0),
            cooldown=data.get("cooldown", 0.0),
            chi_gain=data.get("chi_gain", 0.0),
            weapon_restriction=data.get("weapon_restriction", []),
            description=data.get("description", ""),
            status=data.get("status", ""),
            base_damage=data.get("base_damage", 0),
            weapon_damage_percent=data.get("weapon_damage_percent", 0),
            element_damage=element_damage,
            target_type=data.get("target_type", "enemy"),
            area_size=data.get("area_size", 0.0),
            push_back=data.get("push_back", 0.0),
            duration=data.get("duration", 0.0),
            icon=data.get("icon", "")
        )
    
    def to_csv_row(self) -> List[str]:
        """Конвертация в строку CSV"""
        return [
            str(self.id),
            self.name,
            self.skill_class.value if isinstance(self.skill_class, SkillClass) else str(self.skill_class),
            str(self.level),
            str(self.range),
            str(self.magic_cost),
            str(self.cast_time),
            str(self.apply_time),
            str(self.cooldown),
            str(self.chi_gain),
            str(self.base_damage),
            str(self.weapon_damage_percent),
            self.status
        ]
    
    @classmethod
    def from_csv_row(cls, row: List[str]) -> 'Skill':
        """Создание из строки CSV"""
        return cls(
            id=int(row[0]) if len(row) > 0 else 0,
            name=row[1] if len(row) > 1 else "",
            skill_class=row[2] if len(row) > 2 else "неизвестно",
            level=int(row[3]) if len(row) > 3 else 1,
            range=float(row[4]) if len(row) > 4 and row[4] else 0.0,
            magic_cost=int(row[5]) if len(row) > 5 and row[5] else 0,
            cast_time=float(row[6]) if len(row) > 6 and row[6] else 0.0,
            apply_time=float(row[7]) if len(row) > 7 and row[7] else 0.0,
            cooldown=float(row[8]) if len(row) > 8 and row[8] else 0.0,
            chi_gain=float(row[9]) if len(row) > 9 and row[9] else 0.0,
            base_damage=int(row[10]) if len(row) > 10 and row[10] else 0,
            weapon_damage_percent=int(row[11]) if len(row) > 11 and row[11] else 0,
            status=row[12] if len(row) > 12 else ""
        )
    
    def get_total_cast_time(self) -> float:
        """Полное время каста (подготовка + применение)"""
        return self.cast_time + self.apply_time
    
    def get_description_formatted(self) -> str:
        """Получить форматированное описание"""
        lines = []
        lines.append(f"=== {self.name} (Уровень {self.level}) ===")
        lines.append(f"Класс: {self.skill_class.value if isinstance(self.skill_class, SkillClass) else self.skill_class}")
        lines.append(f"Дистанция: {self.range} м | Маг.энергия: {self.magic_cost}")
        lines.append(f"Каст: {self.cast_time} сек + {self.apply_time} сек | КД: {self.cooldown} сек")
        
        if self.status:
            lines.append(f"Статус: {self.status}")
        
        if self.description:
            lines.append(f"Описание: {self.description}")
        
        damage_parts = []
        if self.base_damage > 0:
            damage_parts.append(f"базовый {self.base_damage}")
        if self.weapon_damage_percent > 0:
            damage_parts.append(f"{self.weapon_damage_percent}% от оружия")
        if self.element_damage:
            for element, dmg in self.element_damage.items():
                element_name = element.value if isinstance(element, ElementType) else str(element)
                damage_parts.append(f"{dmg} {element_name}")
        
        if damage_parts:
            lines.append("Урон: " + " + ".join(damage_parts))
        
        if self.push_back > 0:
            lines.append(f"Отталкивание: {self.push_back} м")
        
        if self.area_size > 0:
            lines.append(f"Радиус: {self.area_size} м")
        
        return "\n".join(lines)


class SkillDatabase:
    """
    Основной класс для работы с базой данных скиллов и баффов
    Загружает, сохраняет, ищет и фильтрует скиллы и баффы
    """
    
    def __init__(self, json_path: str = "asgard_skills.json"):
        # Используем resource_path для поиска файла
        from utils import resource_path
        full_path = resource_path(json_path)
        self.json_path = Path(full_path) if full_path else Path(json_path)
        self.skills: Dict[int, Skill] = {}
        self.buffs: Dict[int, Buff] = {}
        self.skills_by_name: Dict[str, List[Skill]] = {}
        self.buffs_by_name: Dict[str, List[Buff]] = {}
        self.last_update = time.time()
        self.demo_mode = False
        
        # Загружаем данные
        self.load()
        
        # Если нет скиллов, создаём демо
        if len(self.skills) == 0:
            self.create_demo_skills()
            self.demo_mode = True
            self.save()
    
    def load(self):
        """Загрузка скиллов и баффов из JSON файла"""
        if not self.json_path.exists():
            print(f"Файл {self.json_path} не найден")
            return
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Обработка скиллов
            if isinstance(data, list):
                # Старый формат - список
                for item in data:
                    skill = Skill.from_dict(item)
                    self.skills[skill.id] = skill
            elif isinstance(data, dict):
                # Новый формат - словарь {id: skill_data} + возможно "buffs"
                for key, value in data.items():
                    if key == "buffs" and isinstance(value, dict):
                        # Загружаем баффы
                        for buff_id, buff_data in value.items():
                            buff = Buff.from_dict(buff_data)
                            self.buffs[buff.id] = buff
                    elif isinstance(value, dict):
                        # Загружаем скиллы
                        skill = Skill.from_dict(value)
                        self.skills[skill.id] = skill
            
            # Строим индексы
            self._build_name_index()
            
            print(f"Загружено {len(self.skills)} скиллов и {len(self.buffs)} баффов")
            
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
    
    def save(self):
        """Сохранение скиллов и баффов в JSON файл"""
        data = {}
        for skill_id, skill in self.skills.items():
            data[str(skill_id)] = skill.to_dict()
        
        # Добавляем баффы, если они есть
        if self.buffs:
            buffs_dict = {}
            for buff_id, buff in self.buffs.items():
                buffs_dict[str(buff_id)] = buff.to_dict()
            data["buffs"] = buffs_dict
        
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            print(f"Сохранено {len(self.skills)} скиллов и {len(self.buffs)} баффов в {self.json_path}")
            return True
        except Exception as e:
            print(f"Ошибка сохранения данных: {e}")
            return False
    
    def _build_name_index(self):
        """Построение индекса по именам скиллов и баффов"""
        self.skills_by_name = {}
        for skill in self.skills.values():
            name_lower = skill.name.lower()
            if name_lower not in self.skills_by_name:
                self.skills_by_name[name_lower] = []
            self.skills_by_name[name_lower].append(skill)
        
        self.buffs_by_name = {}
        for buff in self.buffs.values():
            name_lower = buff.name.lower()
            if name_lower not in self.buffs_by_name:
                self.buffs_by_name[name_lower] = []
            self.buffs_by_name[name_lower].append(buff)
    
    # ---------- Методы для работы со скиллами ----------
    
    def get_skill(self, skill_id: int) -> Optional[Skill]:
        """Получить скилл по ID"""
        return self.skills.get(skill_id)
    
    def get_skill_by_name(self, name: str, exact: bool = False) -> List[Skill]:
        """Найти скиллы по имени"""
        name_lower = name.lower()
        if exact:
            return self.skills_by_name.get(name_lower, [])
        else:
            results = []
            for skill_name, skills in self.skills_by_name.items():
                if name_lower in skill_name:
                    results.extend(skills)
            return results
    
    def get_skills_by_class(self, skill_class: SkillClass) -> List[Skill]:
        """Получить скиллы по классу"""
        if isinstance(skill_class, str):
            try:
                skill_class = SkillClass(skill_class)
            except ValueError:
                pass
        
        results = []
        for skill in self.skills.values():
            if skill.skill_class == skill_class:
                results.append(skill)
        return results
    
    def get_skills_by_status(self, status: str) -> List[Skill]:
        """Получить скиллы по статусу (Демон, Дух зла и т.д.)"""
        results = []
        status_lower = status.lower()
        for skill in self.skills.values():
            if status_lower in skill.status.lower():
                results.append(skill)
        return results
    
    def add_skill(self, skill: Skill) -> bool:
        """Добавить новый скилл"""
        if skill.id in self.skills:
            return False  # Уже существует
        self.skills[skill.id] = skill
        self._build_name_index()
        return True
    
    def update_skill(self, skill: Skill) -> bool:
        """Обновить существующий скилл"""
        if skill.id not in self.skills:
            return False
        self.skills[skill.id] = skill
        self._build_name_index()
        return True
    
    def delete_skill(self, skill_id: int) -> bool:
        """Удалить скилл"""
        if skill_id not in self.skills:
            return False
        del self.skills[skill_id]
        self._build_name_index()
        return True
    
    # ---------- Методы для работы с баффами ----------
    
    def get_buff(self, buff_id: int) -> Optional[Buff]:
        """Получить бафф по ID"""
        return self.buffs.get(buff_id)
    
    def get_buff_by_name(self, name: str, exact: bool = False) -> List[Buff]:
        """Найти баффы по имени"""
        name_lower = name.lower()
        if exact:
            return self.buffs_by_name.get(name_lower, [])
        else:
            results = []
            for buff_name, buffs in self.buffs_by_name.items():
                if name_lower in buff_name:
                    results.extend(buffs)
            return results
    
    def get_buffs_by_class(self, skill_class: SkillClass) -> List[Buff]:
        """Получить баффы по классу (если указано ограничение)"""
        results = []
        for buff in self.buffs.values():
            if buff.skill_class is None or buff.skill_class == skill_class:
                results.append(buff)
        return results
    
    def add_buff(self, buff: Buff) -> bool:
        """Добавить новый бафф"""
        if buff.id in self.buffs:
            return False
        self.buffs[buff.id] = buff
        self._build_name_index()
        return True
    
    def update_buff(self, buff: Buff) -> bool:
        """Обновить существующий бафф"""
        if buff.id not in self.buffs:
            return False
        self.buffs[buff.id] = buff
        self._build_name_index()
        return True
    
    def delete_buff(self, buff_id: int) -> bool:
        """Удалить бафф"""
        if buff_id not in self.buffs:
            return False
        del self.buffs[buff_id]
        self._build_name_index()
        return True
    
    # ---------- Общие методы ----------
    
    def import_from_csv(self, csv_path: str) -> int:
        """Импорт скиллов из CSV файла (баффы не импортируются через CSV)"""
        imported = 0
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Пропускаем заголовок
                
                for row in reader:
                    if len(row) >= 7:
                        skill = Skill.from_csv_row(row)
                        if skill.id not in self.skills:
                            self.skills[skill.id] = skill
                            imported += 1
                        else:
                            # Обновляем существующий
                            self.skills[skill.id] = skill
                            imported += 1
            
            self._build_name_index()
            self.save()
            return imported
            
        except Exception as e:
            print(f"Ошибка импорта из CSV: {e}")
            return 0
    
    def export_to_csv(self, csv_path: str) -> bool:
        """Экспорт скиллов в CSV файл (баффы не экспортируются)"""
        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                # Заголовок
                writer.writerow([
                    "id", "name", "class", "level", "range", 
                    "magic_cost", "cast_time", "apply_time", 
                    "cooldown", "chi_gain", "base_damage", 
                    "weapon_damage_percent", "status"
                ])
                
                for skill in self.skills.values():
                    writer.writerow(skill.to_csv_row())
            
            return True
        except Exception as e:
            print(f"Ошибка экспорта в CSV: {e}")
            return False
    
    def create_demo_skills(self):
        """Создание демонстрационных скиллов на основе скриншотов"""
        demo_skills = [
            Skill(
                id=1,
                name="Тёмное огненное клеймо",
                level=10,
                skill_class=SkillClass.MAGE,
                range=30,
                magic_cost=265,
                cast_time=1.5,
                apply_time=0.8,
                cooldown=3.0,
                chi_gain=0.15,
                weapon_restriction=["магическое оружие", "без оружия"],
                description="Подчиняет заклейменного противника воле мага",
                status="Демон",
                base_damage=100,
                weapon_damage_percent=100,
                element_damage={ElementType.FIRE: 3620}
            ),
            Skill(
                id=2,
                name="Тёмные крылья феникса",
                level=10,
                skill_class=SkillClass.MAGE,
                range=10,
                magic_cost=445,
                cast_time=1.0,
                apply_time=1.0,
                cooldown=8.0,
                chi_gain=0.15,
                weapon_restriction=["магическое оружие", "без оружия"],
                description="Маг призывает феникса, который атакует всех противников на линии длиной 18 м и отбрасывает их на 18 м. Отталкивание не действует на игроков. Зона поражения увеличена на 50%.",
                status="Демон",
                base_damage=100,
                weapon_damage_percent=100,
                element_damage={ElementType.FIRE: 5395},
                area_size=18,
                push_back=18
            ),
            Skill(
                id=3,
                name="Ледяная стрела",
                level=5,
                skill_class=SkillClass.MAGE,
                range=25,
                magic_cost=120,
                cast_time=1.2,
                apply_time=0.5,
                cooldown=2.0,
                chi_gain=0.1,
                weapon_restriction=["магическое оружие"],
                description="Выпускает ледяную стрелу в противника",
                base_damage=200,
                weapon_damage_percent=80,
                element_damage={ElementType.WATER: 500}
            ),
            Skill(
                id=4,
                name="Огненный шар",
                level=5,
                skill_class=SkillClass.MAGE,
                range=20,
                magic_cost=150,
                cast_time=1.5,
                apply_time=0.3,
                cooldown=2.5,
                chi_gain=0.12,
                weapon_restriction=["магическое оружие"],
                description="Запускает огненный шар, наносящий урон в области",
                base_damage=250,
                weapon_damage_percent=90,
                element_damage={ElementType.FIRE: 600},
                area_size=5
            ),
            Skill(
                id=5,
                name="Лечение",
                level=5,
                skill_class=SkillClass.PRIEST,
                range=20,
                magic_cost=200,
                cast_time=2.0,
                apply_time=0.5,
                cooldown=4.0,
                chi_gain=0.2,
                weapon_restriction=["магическое оружие"],
                description="Восстанавливает здоровье цели",
                target_type="party",
                base_damage=500
            ),
            Skill(
                id=6,
                name="Удар берсерка",
                level=5,
                skill_class=SkillClass.WARRIOR,
                range=3,
                magic_cost=50,
                cast_time=0.5,
                apply_time=0.8,
                cooldown=6.0,
                chi_gain=0.25,
                weapon_restriction=["топор", "меч"],
                description="Мощный удар, оглушающий противника",
                base_damage=400,
                weapon_damage_percent=150,
                element_damage={ElementType.PHYSICAL: 300},
                duration=2.0
            ),
            Skill(
                id=7,
                name="Темное несогласие",
                level=10,
                skill_class=SkillClass.MAGE,
                range=30,
                magic_cost=295,
                cast_time=0.5,
                apply_time=2.0,
                cooldown=20.0,
                chi_gain=0.1,
                weapon_restriction=["магическое оружие", "без оружия"],
                description="Прерывает заклинания и запрещает применять их на 5 сек. Обездвиживает цель на 2 сек.",
                status="Дух зла"
            ),
            Skill(
                id=8,
                name="Тёмный бьющий ключ",
                level=10,
                skill_class=SkillClass.MAGE,
                range=30,
                magic_cost=265,
                cast_time=1.0,
                apply_time=1.0,
                cooldown=3.0,
                chi_gain=0.1,
                weapon_restriction=["магическое оружие", "без оружия"],
                description="Из земли вырывается горячий гейзер. Наносит урон +100% урона снаряжения +3390 ед. урона водой. С вероятностью 95% замедляет на 40% на 8 сек.",
                status="Демон",
                base_damage=100,
                weapon_damage_percent=100,
                element_damage={ElementType.WATER: 3390}
            )
        ]
        
        for skill in demo_skills:
            self.skills[skill.id] = skill
        
        demo_buffs = [
            Buff(
                id=6001,
                name="Тёмное сосредоточение",
                duration=15,
                channeling_bonus=20,
                description="Увеличивает скорость подготовки на 20% на 15 сек",
                skill_class=SkillClass.MAGE
            ),
            Buff(
                id=6002,
                name="Свиток скорости",
                duration=30,
                channeling_bonus=15,
                description="Увеличивает скорость подготовки на 15% на 30 сек",
                skill_class=None
            )
        ]
        for buff in demo_buffs:
            self.buffs[buff.id] = buff
        
        self._build_name_index()
        print(f"Создано {len(demo_skills)} демо-скиллов и {len(demo_buffs)} демо-баффов")

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику базы данных"""
        stats = {
            "total_skills": len(self.skills),
            "total_buffs": len(self.buffs),
            "skills_by_class": {},
            "skills_by_level": {},
            "skills_by_status": {},
            "demo_mode": self.demo_mode
        }
        
        for skill in self.skills.values():
            class_name = skill.skill_class.value if isinstance(skill.skill_class, SkillClass) else str(skill.skill_class)
            stats["skills_by_class"][class_name] = stats["skills_by_class"].get(class_name, 0) + 1
            stats["skills_by_level"][skill.level] = stats["skills_by_level"].get(skill.level, 0) + 1
            if skill.status:
                stats["skills_by_status"][skill.status] = stats["skills_by_status"].get(skill.status, 0) + 1
        
        return stats
    
    def get_all_skills_simple(self) -> List[Dict]:
        """Получить упрощенный список скиллов и баффов для отображения в main.py"""
        simple_list = []
        
        # Добавляем скиллы
        for skill in self.skills.values():
            simple_list.append({
                "id": skill.id,
                "name": skill.name,
                "class": skill.skill_class.value if isinstance(skill.skill_class, SkillClass) else str(skill.skill_class),
                "cast_time": skill.cast_time,
                "apply_time": skill.apply_time,
                "cooldown": skill.cooldown,
                "range": skill.range,
                "magic_cost": skill.magic_cost,
                "status": skill.status,
                "icon": skill.icon
            })
        
        # Добавляем баффы
        for buff in self.buffs.values():
            simple_list.append({
                "id": buff.id,
                "name": buff.name,
                "duration": buff.duration,
                "channeling_bonus": buff.channeling_bonus,
                "description": buff.description,
                "class": buff.skill_class.value if buff.skill_class else "все",
                "icon": buff.icon if buff.icon else ""
            })
        
        return sorted(simple_list, key=lambda x: x["id"])


if __name__ == "__main__":
    print("=" * 50)
    print("Skill Database Test")
    print("=" * 50)
    db = SkillDatabase("test_skills.json")
    stats = db.get_stats()
    print(f"\nВсего скиллов: {stats['total_skills']}")
    print(f"Всего баффов: {stats['total_buffs']}")
    print(f"Демо-режим: {stats['demo_mode']}")
    print("\nПо классам:")
    for class_name, count in stats['skills_by_class'].items():
        print(f"  {class_name}: {count}")
    print("\n" + "=" * 50)
    print("Демо-скиллы:")
    print("=" * 50)
    for skill_id, skill in db.skills.items():
        print("\n" + skill.get_description_formatted())
        print("-" * 30)
    print("\n" + "=" * 50)
    print("Демо-баффы:")
    print("=" * 50)
    for buff_id, buff in db.buffs.items():
        print(f"\nID: {buff.id}")
        print(f"Название: {buff.name}")
        print(f"Длительность: {buff.duration} сек")
        print(f"Бонус к пению: {buff.channeling_bonus}%")
        print(f"Описание: {buff.description}")
        print(f"Класс: {buff.skill_class.value if buff.skill_class else 'все'}")
        print("-" * 30)
    db.export_to_csv("test_skills.csv")
    print("\n✅ Экспорт в test_skills.csv выполнен")
    simple_list = db.get_all_skills_simple()
    print("\nУпрощенный список для main.py:")
    for skill in simple_list[:5]:
        print(f"  {skill['id']}: {skill['name']} ({skill['class']}) - Каст: {skill['cast_time']}с, КД: {skill['cooldown']}с")
    if len(simple_list) > 5:
        print(f"  ... и ещё {len(simple_list) - 5}")