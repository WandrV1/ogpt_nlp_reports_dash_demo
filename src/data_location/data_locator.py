import os
from datetime import datetime

import pandas as pd

from .utils import midpoint_date


class DataLocator:

    def __init__(self, data_path: str, warnings_path: str | None):
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file {data_path} not found")
        if warnings_path is not None and not os.path.exists(warnings_path):
            raise FileNotFoundError(f"Warnings file {warnings_path} not found")
        self.data = self._read_data_file(data_path)
        # TODO убрать этот код. Он нужен для демонстрации
        self.data['Скважина'] = 'Скважина'
        self.data['Месторождение'] = 'Месторождение'

        self.warnings = pd.read_excel(warnings_path) if warnings_path is not None else None

    def _read_data_file(self, path: str) -> pd.DataFrame:
        data = pd.read_excel(path)
        data['Начало_исследования'] = pd.to_datetime(data['Начало_исследования'], format='%d.%m.%Y')
        data['Окончание_исследования'] = pd.to_datetime(data['Окончание_исследования'], format='%d.%m.%Y')
        data['Дата'] = data.apply(lambda row: midpoint_date(row['Начало_исследования'], row['Окончание_исследования']), axis=1)
        return data

    def locate_records(self, well: str, field: str, param: str, param_type: str | None, start_date: datetime | None, end_date: datetime | None) -> tuple[pd.DataFrame, pd.DataFrame]:
        df = self.data[(self.data['Скважина'].str.lower() == well.lower()) & (self.data['Месторождение'].str.lower() == field.lower())]
        # Фильтрация по датам
        if start_date is not None:
            df = df[df['Начало_исследования'] >= start_date]
        if end_date is not None:
            df = df[df['Окончание_исследования'] <= end_date]
        df.sort_values(by='Дата', inplace=True)
        for param, param_type in self._adjust_search_params(param, param_type):
            df_selected = df[df['Параметр'] == param]
            if param_type is not None:
                df_selected = df_selected[df_selected['Тип'] == param_type]
            if not df_selected.empty:
                return df_selected, self._locate_warnings(df_selected)
        return df.head(0), self.warnings.head(0)

    def _locate_warnings(self, records: pd.DataFrame):
        warnings = self.warnings[self.warnings['Файл'].isin(records['Файл'])]
        warnings = warnings[warnings['Параметр'].isin(records['Параметр'])]
        warnings = warnings[warnings['Тип'].isin(records['Тип'])]
        return warnings

    def _adjust_search_params(self, param: str, param_type: str | None) -> list[tuple[str, str | None]]:
        if param == 'Забойное давление':
            if param_type is None:
                return [('Забойное давление', 'ВДП'),
                        ('Забойное давление', 'На глубине замера'),
                        ('Забойное давление', 'ВНК')]
            elif param_type == 'ВДП':
                return [('Забойное давление', 'ВДП')]
            elif param_type == 'ВНК':
                return [('Забойное давление', 'ВНК')]
            elif param_type == 'На глубине замера':
                return [('Забойное давление', 'На глубине замера')]
            elif param_type == 'На кровлю':
                return [('Забойное давление', 'На кровлю')]
            elif param_type == 'ГНК':
                return [('Забойное давление', 'ГНК')]
            else:
                raise NotImplementedError(f'Поиск параметра {param} {param_type} не предусмотрен')
        elif param == 'Пластовое давление':
            if param_type is None:
                return [('Пластовое давление', 'ВДП'),
                        ('Пластовое давление', 'На глубине замера'),
                        ('Пластовое давление', 'ВНК')]
            elif param_type == 'ВДП':
                return [('Пластовое давление', 'ВДП')]
            elif param_type == 'ВНК':
                return [('Пластовое давление', 'ВНК')]
            elif param_type == 'На глубине замера':
                return [('Пластовое давление', 'На глубине замера')]
            elif param_type == 'На кровлю':
                return [('Пластовое давление', 'На кровлю')]
            elif param_type == 'ГНК':
                return [('Пластовое давление', 'ГНК')]
            else:
                raise NotImplementedError(f'Поиск параметра {param} {param_type} не предусмотрен')
        elif param == 'Скин-фактор':
            if param_type is None:
                return [('Скин-фактор', 'Интегральный'),
                        ('Скин-фактор', 'Механический')]
            elif param_type == 'Интегральный':
                return [('Скин-фактор', 'Интегральный')]
            elif param_type == 'Механический':
                return [('Скин-фактор', 'Механический')]
            else:
                raise NotImplementedError(f'Поиск параметра {param} {param_type} не предусмотрен')
        elif param == 'Проницаемость':
            if param_type is None:
                return [('Проницаемость', None)]
            elif param_type == 'По жидкости' or param_type == 'По воде':
                return [('Проницаемость', 'По жидкости')]
            elif param_type == 'По нефти':
                return [('Проницаемость', 'По нефти')]
            else:
                raise NotImplementedError(f'Поиск параметра {param} {param_type} не предусмотрен')
        elif param == 'Фазовая проницаемость':
            if param_type is None:
                return [('Фазовая проницаемость', 'По нефти')]
            elif param_type == 'По жидкости' or param_type == 'По воде':
                return [('Фазовая проницаемость', 'По жидкости')]
            elif param_type == 'По нефти':
                return [('Фазовая проницаемость', 'По нефти')]
            else:
                raise NotImplementedError(f'Поиск параметра {param} {param_type} не предусмотрен')
        elif param == 'Коэффициент продуктивности' or param == 'Коэффициент приемистости':
            return [('Коэффициент продуктивности', None),
                    ('Коэффициент приемистости', None)]
        else:
            raise NotImplementedError(f'Поиск параметра {param} {param_type} не предусмотрен')
