import PySimpleGUI as sg
import json
from datetime import datetime
from PIL import Image, ImageTk
from PIL import Image, ImageOps
import io
import base64
import os
import tempfile


last_sort_key = 'name'
last_sort_order = False
update_window = None
add_window = None
sort_key_map = {'Name': 'name', 'Date': 'date', 'Duration': 'duration'}

def resize_image(image, max_size=(200, 200)):
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.ANTIALIAS
    
    image.thumbnail(max_size, resample)
    new_image = Image.new("RGB", max_size, (255, 255, 255))
    padding = (int((max_size[0] - image.size[0]) / 2), int((max_size[1] - image.size[1]) / 2))
    new_image.paste(image, padding)
    
    return new_image

def update_image(window, path, key):
    try:
        if not os.path.exists(path):
            sg.popup_error(f"File does not exist: {path}")
            return
        
        img = Image.open(path)
        img.verify()
        img.close()
        
        img = Image.open(path)
        img = resize_image(img, max_size=(200, 200))

    except IOError as e:
        sg.popup_error("IOError: Failed to load image. Make sure the image file is not corrupted and is in a supported format.", str(e))
    except Exception as e:
        sg.popup_error("An unexpected error occurred while loading the image", str(e))


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
    photo_indicator = "[Photo]" if activity.get('photo') else ""
    return f"{name} {date} {time} {duration} {photo_indicator}"


def add_activity_window():
    layout = [
        [sg.Text("Name of Activity:", font=("Helvetica", 10)), sg.InputText(key='name')],
        [sg.Text("Date:", font=("Helvetica", 10)), sg.Input(key='date'), sg.CalendarButton("Choose Date", target='date', key='date_btn', format='%Y-%m-%d')],
        [sg.Text("Time:", font=("Helvetica", 10)), sg.Combo([f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in range(0, 60, 15)], key='time')],
        [sg.Text("Duration (minutes):", font=("Helvetica", 10)), sg.InputText(key='duration')],
        [sg.Text("Photo:", font=("Helvetica", 10)), sg.InputText(enable_events=True, key='photo_path'), sg.FileBrowse(target='photo_path')], 
        [sg.Image(key='photo_preview')],
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
        [sg.Text("Comments:"), sg.Multiline(default_text=comments_str, size=(35, 3), key='comments_display')],
        [sg.Text("Photo:", font=("Helvetica", 10))], 
        [sg.InputText(default_text=activity.get('photo', ''), enable_events=True, key='photo_path'), sg.FileBrowse(target='photo_path')], 
        [sg.Image(filename=activity.get('photo', ''), key='photo_preview')],
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
            sg.Button("Add New Activity", font=("Helvetica", 10)),
            sg.Button("Remove Selected Activity", font=("Helvetica", 10)),
            sg.Button("Update Selected Activity", font=("Helvetica", 10))
        ],
        [
            sg.Text('Sort by', font=("Helvetica", 10)), sg.Combo(sort_keys, default_value=sort_keys[0], key='sort_combo', font=("Helvetica", 10))
        ],
        [sg.Listbox(values=[], size=(70, 10), font=('Courier New', 10), key='activities_list')],
        [
            sg.Text('Search for an activity', font=("Helvetica", 10)), sg.InputText(key='search_input'),
            sg.Button('Search', font=("Helvetica", 10))
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
        if not add_window:
            add_window = add_activity_window()
        while True:
            event, values = add_window.read()

            if event in (sg.WIN_CLOSED, 'Cancel'):
                add_window.close()
                add_window = None
                break
            elif event == 'Save':
                new_activity = {
                    'name': values['name'],
                    'date': values['date'],
                    'time': values['time'],
                    'duration': values['duration'],
                    'comments': [],
                    'photo': values['photo_path']
                }
                activities.append(new_activity)
                save_activities(activities)
                add_window.close()
                add_window = None
                sorted_activities = get_sorted_activities(activities, last_sort_key, last_sort_order)
                window['activities_list'].update(values=[format_activity_for_display(act) for act in sorted_activities])
                break
            elif event == 'photo_path':
                update_image(add_window if add_window else update_window, values['photo_path'], 'photo_preview')


    elif event == 'Update Selected Activity' and values['activities_list']:
        selected_activity = next((act for act in activities if format_activity_for_display(act) == values['activities_list'][0]), None)
        if selected_activity:
            if not update_window:
                update_window = update_activity_window(selected_activity)
            while True:
                event, values = update_window.read()
                if event in (sg.WIN_CLOSED, 'Cancel'):
                    update_window.close()
                    update_window = None
                    break
                elif event == 'Save':
                    edited_comments = values['comments_display'].strip().split('\n')
                    selected_activity.update({
                        'name': values['name'],
                        'date': values['date'],
                        'time': values['time'],
                        'duration': values['duration'],
                        'comments': edited_comments,
                        'photo': values['photo_path']
                    })
                    save_activities(activities)
                    update_window.close()
                    update_window = None
                    sorted_activities = get_sorted_activities(activities, last_sort_key, last_sort_order)
                    window['activities_list'].update(values=[format_activity_for_display(act) for act in sorted_activities])
                    break
                elif event == 'photo_path':
                    update_image(add_window if add_window else update_window, values['photo_path'], 'photo_preview')

    elif event == 'Remove Selected Activity':
        selected_activity_display = values['activities_list'][0] if values['activities_list'] else None
        if selected_activity_display:
            for activity in activities:
                if format_activity_for_display(activity) == selected_activity_display:
                    activities.remove(activity)
                    save_activities(activities)
                    break
            
            sorted_activities = get_sorted_activities(activities, last_sort_key, last_sort_order)
            window['activities_list'].update(values=[format_activity_for_display(act) for act in sorted_activities])

    elif event == 'Search':
        search_term = values['search_input']
        selected_sort_key_gui = values['sort_combo']
        programmatic_sort_key = sort_key_map[selected_sort_key_gui]
        filtered_and_sorted_activities = search_activities(activities, search_term, programmatic_sort_key, last_sort_order)
        window['activities_list'].update(values=[format_activity_for_display(act) for act in filtered_and_sorted_activities])
    elif event == 'Refresh':
        selected_sort_key_gui = values['sort_combo']
        programmatic_sort_key = sort_key_map[selected_sort_key_gui]
        sorted_activities = get_sorted_activities(activities, programmatic_sort_key, last_sort_order)
        window['activities_list'].update(values=[format_activity_for_display(act) for act in sorted_activities])

if add_window:
    add_window.close()
if update_window:
    update_window.close()

window.close()