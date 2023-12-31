import json
from datetime import datetime, timedelta
from System.units.time_event import TimeEvent
from System.units.message import Message
import logging
from System import config_manager


def start():
    logging.info('Запуск модуля data_manager')
    global __fired_events_file
    global __events_file
    global __council_file

    __fired_events_file = config_manager.fired_events_file()
    __events_file = config_manager.events_file()
    __council_file = config_manager.council_file()


def __save_json(file_name, args):
    # logger.info('Сохранены данные', data=args)
    with open(file_name, 'w') as file:
        json.dump(args, file, indent=4, ensure_ascii=False)


def __load_json(file_name: str):
    with open(file_name, 'r') as file:
        try:
            data = json.load(file)
        except json.decoder.JSONDecodeError:
            return None
        # logger.info('Загружены данные', data=data)
        return data


def __load_txt(file_name: str) -> list[str]:
    with open(file_name, 'r', encoding='utf-8') as file:
        return file.readlines()


def is_council(id: str) -> bool:
    users = __load_json(__council_file)
    return id in users.keys()


def council_ids() -> list[str]:
    global __council_file
    return __load_json(__council_file).keys()


def store_event(event):
    """
    Сохраняет событие в файл
    :param event: объект события
    """
    events = __load_json(__events_file)
    if len(events) == 0:
        events = [event.__dict__()]
    else:
        flag = False
        for index in range(len(events)):
            ev = TimeEvent.get_datetime(events[index])
            if event.__time < ev:
                flag = True
                event = event.to_dict()
                events.insert(index, event)
                break
        if not flag:
            events.append(event.to_dict())
    __save_json(__events_file, events)


def get_nearest_event(old_event=None) -> TimeEvent:
    """
    Возвращает ближайшее событие
    :params old_event: исполнившееся событие
    """
    events = __load_json(config_manager.events_file())  # считывает список событий из файла
    if events is None or len(events) == 0:  # если событий нет, то возвращает None
        return None
    else:
        if old_event is not None:  # если передано старое событие, то удаляет его из списка
            events.pop(0)
            __save_json(config_manager.events_file(), events)  # записывает измененный список обратно в файл
        if len(events) == 0:
            return None
        nearest_event = events[0]  # получаем ближайшее событие
        event_class = eval(nearest_event['class_name'])  # создаем объект того же класса, что и nearest_event

        return event_class.from_dict(nearest_event)


def _check_fired_events():
    """
    Используется единожды при запуске, возвращает ближайшее не просроченное событие
    """

    events = __load_json(config_manager.events_file())
    if len(events) != 0:
        fired_events = []
        actual_events = []
        for event in events:
            delta = datetime.now() - TimeEvent.get_datetime(event)
            if delta > timedelta(minutes=1):
                fired_events.append(event)
            else:
                actual_events.append(event)

        # записываем список запланированных событий без просрочек

        __save_json(config_manager.events_file(), actual_events)

        if len(fired_events) != 0:
            load_fired_events = __load_json(config_manager.fired_events_file())  # загружаем список просрочек
            load_fired_events += fired_events  # добавляем в список новые просрочки
            __save_json(config_manager.fired_events_file(), load_fired_events)  # загружаем все обратно


def get_fired_events():
    """
    Возвращает список просроченных событий
    """
    fired_events = __load_json(__fired_events_file)

    if len(fired_events) == 0:
        return None

    for i in (range(len(fired_events))):
        event_class = eval(fired_events[i]['class_name'])
        fired_events[i] = event_class.from_dict(fired_events[i])

    return fired_events


def id_to_names(ids: list):
    """
    Получиет имена пользователей и возвращает их id
    :param ids: список фамилий пользователей
    :return: список соответствующих фамилиям id
    """
    names = []
    ids = [ids] if isinstance(ids, str) else ids
    users = __load_json(__council_file)
    for id in ids:
        if id in users.keys():
            names.append(users[id]['name'])

    return names


def names_to_id(names: list[str]):
    """
    Получиет имена пользователей и возвращает их id
    :param names: список фамилий пользователей
    :return: список соответствующих фамилиям id
    """
    names = [names] if isinstance(names, str) else names
    users = __load_json(__council_file)
    for i in range(len(names)):
        for id, data in users.items():
            if names[i].startswith(data['name_index']) or names[i].startswith(data['surname']):
                names[i] = id
    return names


def about_club():
    return __load_txt(config_manager.about_club_file())


def about_projects():
    return __load_txt(config_manager.about_projects_file())


def join_club():
    return __load_txt(config_manager.join_club_file())
