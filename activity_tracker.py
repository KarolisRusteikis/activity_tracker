import PySimpleGUI as sg
import json
from datetime import datetime

last_sort_key = 'name'
last_sort_order = False

def ensure_db_exists(filename="activities.json"):
    try:
        with open(filename, "r") as file:
            pass
    except FileNotFoundError:
        with open(filename, "w") as file:
            json.dump([], file)

ensure_db_exists()

def load_activities(filename="activities.json"):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_activities(activities, filename="activities.json"):
    with open(filename, "w") as file:
        json.dump(activities, file, indent=4)

def format_activity_for_display(activity):
    name = "{:<20}".format(activity['name'])
    date = "{:<10}".format(activity['date'])
    time = "{:<5}".format(activity['time'])
    duration = "{:>3} min".format(activity['duration'])
    return f"{name} {date} {time} {duration}"

def add_activity_window():
    layout = [
        [sg.Text("Name of Activity:"), sg.InputText(key='name')],
        [sg.Text("Date:"), sg.Input(key='date'), sg.CalendarButton("Choose Date", target='date', key='date_btn', format='%Y-%m-%d')],
        [sg.Text("Time:"), sg.Combo([f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in range(0, 60, 15)], key='time')],
        [sg.Text("Duration (minutes):"), sg.InputText(key='duration')],
        [sg.Button("Save"), sg.Button("Cancel")]
    ]
    return sg.Window("Add New Activity", layout, finalize=True)

def update_activity_window(activity):
    comments_str = '\n'.join(activity.get('comments', []))
    layout = [
        [sg.Text("Name of Activity:"), sg.InputText(activity['name'], key='name')],
        [sg.Text("Date:"), sg.Input(default_text=activity['date'], key='date'), sg.CalendarButton("Choose Date", target='date', key='date_btn', format='%Y-%m-%d')],
        [sg.Text("Time:"), sg.Combo([f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in range(0, 60, 15)], default_value=activity['time'], key='time')],
        [sg.Text("Duration (minutes):"), sg.InputText(activity['duration'], key='duration')],
        [sg.Text("Comments:"), sg.Multiline(default_text=comments_str, size=(35, 3), disabled=True, key='comments_display')],
        [sg.Text("Add Comment:"), sg.InputText(key='new_comment')],
        [sg.Button("Save"), sg.Button("Cancel")]
    ]
    return sg.Window("Update Activity", layout, finalize=True)

def get_sorted_activities(activities, sort_key, reverse=False):
    try:
        if sort_key == 'duration':
            return sorted(activities, key=lambda x: int(x[sort_key]), reverse=reverse)
        else:
            return sorted(activities, key=lambda x: x[sort_key], reverse=reverse)
    except KeyError:
        return activities

def search_activities(activities, term, sort_key, reverse=False):
    try:
        results = [act for act in activities if term.lower() in act['name'].lower() or term.lower() in act['date'].lower()]
        if sort_key == 'duration':
            return sorted(results, key=lambda x: int(x[sort_key]), reverse=reverse)
        else:
            return sorted(results, key=lambda x: x[sort_key], reverse=reverse)
    except KeyError:
        return results

def create_main_window():
    sort_keys = ['Name', 'Date', 'Duration']
    layout = [
        [sg.Text("ACTIVITY TRACKER v1.3", size=(30, 1), font=("Helvetica", 25))],
        [
            sg.Button("Add New Activity"),
            sg.Button("Remove Selected Activity"),
            sg.Button("Update Selected Activity")
        ],
        [
            sg.Text('Sort by'), sg.Combo(sort_keys, default_value=sort_keys[0], key='sort_combo'),
            sg.Button('Refresh', key='refresh_main')
        ],
        [sg.Listbox(values=[], size=(70, 10), font=('Courier New', 10), key='activities_list')],
        [
            sg.Text('Search for an activity'), sg.InputText(key='search_input'),
            sg.Button('Search')
        ]
    ]
    return sg.Window("Activity Tracker", layout, finalize=True)

window = create_main_window()
activities = load_activities()
window['activities_list'].update(values=[format_activity_for_display(act) for act in get_sorted_activities(activities, 'name')])

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break
    elif event == 'Add New Activity':
        add_window = add_activity_window()
        while True:
            event, values = add_window.read()
            if event in (sg.WIN_CLOSED, 'Cancel'):
                add_window.close()
                break
            elif event == 'Save':
                if 'time' in values:
                    new_activity = {
                        'name': values['name'],
                        'date': values['date'],
                        'time': values['time'],
                        'duration': values['duration'],
                        'comments': []
                    }
                    activities.append(new_activity)
                    save_activities(activities)
                    add_window.close()
                    sorted_activities = get_sorted_activities(activities, last_sort_key, last_sort_order)
                    window['activities_list'].update(values=[format_activity_for_display(act) for act in sorted_activities])
                    break
    elif event == 'Remove Selected Activity' and values['activities_list']:
        selected_activity_info = next((act for act in activities if format_activity_for_display(act) == values['activities_list'][0]), None)
        if selected_activity_info and sg.popup_yes_no('Are you sure you want to remove the selected activity?') == 'Yes':
            activities.remove(selected_activity_info)
            save_activities(activities)
            sorted_activities = get_sorted_activities(activities, last_sort_key, last_sort_order)
            window['activities_list'].update(values=[format_activity_for_display(act) for act in sorted_activities])
    elif event == 'Update Selected Activity' and values['activities_list']:
        selected_activity_info = next((act for act in activities if format_activity_for_display(act) == values['activities_list'][0]), None)
        if selected_activity_info:
            update_window = update_activity_window(selected_activity_info)
            while True:
                event, values = update_window.read()
                if event in (sg.WIN_CLOSED, 'Cancel'):
                    update_window.close()
                    break
                elif event == 'Save':
                    updated_comments = selected_activity_info.get('comments', [])
                    new_comment = values['new_comment'].strip()
                    if new_comment:
                        updated_comments.append(new_comment)
                    
                    updated_activity = {
                        'name': values['name'],
                        'date': values['date'],
                        'time': values['time'],
                        'duration': values['duration'],
                        'comments': updated_comments
                    }
                    index = activities.index(selected_activity_info)
                    activities[index] = updated_activity
                    save_activities(activities)
                    update_window.close()
                    sorted_activities = get_sorted_activities(activities, last_sort_key, last_sort_order)
                    window['activities_list'].update(values=[format_activity_for_display(act) for act in sorted_activities])
                    break
    elif event == 'Search':
        search_term = values['search_input']
        filtered_activities = search_activities(activities, search_term, last_sort_key, last_sort_order)
        sorted_filtered_activities = get_sorted_activities(filtered_activities, last_sort_key, last_sort_order)
        window['activities_list'].update(values=[format_activity_for_display(act) for act in sorted_filtered_activities])
    elif event == 'refresh_main':
        last_sort_key = values['sort_combo'].lower()
        sorted_activities = get_sorted_activities(activities, last_sort_key, last_sort_order)
        window['activities_list'].update(values=[format_activity_for_display(act) for act in sorted_activities])

window.close()

