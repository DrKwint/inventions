from distutils.command.config import config
from pathlib import Path
import re
import shutil

DEBUG = False
global_event_idx = 1


def generate_notification_event(key, content):
    content["${key}"] = key
    with open('./templates/notification_event_template.txt') as template_file:
        entry = template_file.read()
    # use these three lines to do the replacement
    rep = dict((re.escape(k), str(v)) for k, v in content.items())
    pattern = re.compile("|".join(rep.keys()))
    event = pattern.sub(lambda m: rep[re.escape(m.group(0))], entry)
    return event


def generate_completion_event(key, content):
    content["${key}"] = key
    event_icons = {
        'industry': "industry",
        'military': "military",
        'society': "portrait"
    }
    content["${event_icon}"] = event_icons[content["${type}"]]
    event_pictures = {
        'industry': "middleeast_engineer_blueprint",
        "military": "europenorthamerica_before_the_battle",
        'society': "europenorthamerica_rich_and_poor"
    }
    content["${event_picture}"] = event_pictures[content["${type}"]]
    with open('./templates/completion_event_template.txt') as template_file:
        entry = template_file.read()
    # use these three lines to do the replacement
    rep = dict((re.escape(k), str(v)) for k, v in content.items())
    pattern = re.compile("|".join(rep.keys()))
    event = pattern.sub(lambda m: rep[re.escape(m.group(0))], entry)
    return event


def generate_advancement_event(key, content):
    content["${key}"] = key
    with open('./templates/advancement_event_template.txt') as template_file:
        entry = template_file.read()
    # use these three lines to do the replacement
    rep = dict((re.escape(k), str(v)) for k, v in content.items())
    pattern = re.compile("|".join(rep.keys()))
    event = pattern.sub(lambda m: rep[re.escape(m.group(0))], entry)
    return event


def generate_notification(content):
    with open('./templates/notification_template.txt') as template_file:
        entry = template_file.read()
    # use these three lines to do the replacement
    rep = dict((re.escape(k), str(v)) for k, v in content.items())
    pattern = re.compile("|".join(rep.keys()))
    event = pattern.sub(lambda m: rep[re.escape(m.group(0))], entry)
    return event


def generate_modifiers(content):
    config_dir = Path('configs') / content['${script_name}']
    content['${tech_modifier}'] = (config_dir /
                                   'tech_modifier.txt').open().read()
    icons = {
        'industry': 'gear_positive',
        'military': 'rifle_positive',
        'society': 'statue_positive'
    }
    content['${icon}'] = icons[content['${type}']]

    with open('./templates/tech_modifier_template.txt') as template_file:
        entry = template_file.read()
    # use these three lines to do the replacement
    rep = dict((re.escape(k), str(v)) for k, v in content.items())
    pattern = re.compile("|".join(rep.keys()))
    event = pattern.sub(lambda m: rep[re.escape(m.group(0))], entry)
    return event


def generate_localization(content):
    with open('./templates/localization_template.txt') as template_file:
        entry = template_file.read()
    # use these three lines to do the replacement
    rep = dict((re.escape(k), str(v)) for k, v in content.items())
    pattern = re.compile("|".join(rep.keys()))
    event = pattern.sub(lambda m: rep[re.escape(m.group(0))], entry)
    return event


def generate_journal_entry(config):
    global global_event_idx
    je_event_str = ""
    config_dir = Path('configs') / config['${script_name}']
    texts = [
        'add = 1', (config_dir / 'minor.txt').open().read(),
        (config_dir / 'major.txt').open().read(), 'add = 500'
    ]
    modifier = (config_dir / 'advance_modifier.txt').open().read()

    events = []
    for prob, text in zip(config["${event_probs}"], texts):
        content = {}
        content["${script_name}"] = config["${script_name}"]
        event_key = f"invention_events.{global_event_idx}"
        global_event_idx += 1
        je_event_str += f"{prob} = {event_key}\n"
        content["${key}"] = event_key
        content["${add}"] = text
        content["${modifier}"] = modifier
        events.append(generate_advancement_event(event_key, content))
    config["${weekly_event_str}"] = je_event_str[:-1]

    config["${completion_event_idx}"] = global_event_idx
    global_event_idx += 1
    completion_event_idx = config["${completion_event_idx}"]
    notification_event_idx = global_event_idx
    global_event_idx += 1
    completion_config = {
        "${script_name}": config["${script_name}"],
        "${type}": config["${type}"],
        "${notification_event_idx}": notification_event_idx
    }
    events.append(
        generate_completion_event(f"invention_events.{completion_event_idx}",
                                  completion_config))

    events.append(
        generate_notification_event(
            f"invention_events.{notification_event_idx}",
            {"${script_name}": config['${script_name}']}))

    if config['${type}'] == 'industry':
        config["${event_icon_name}"] = "event_industry"
    elif config['${type}'] == 'society':
        config["${event_icon_name}"] = "event_portrait"
    elif config['${type}'] == 'military':
        config["${event_icon_name}"] = "event_military"
    else:
        raise NotImplementedError()

    config_dir = Path('configs') / content['${script_name}']
    config["${show}"] = (config_dir / 'show.txt').open().read()
    config["${possible}"] = (config_dir / 'possible.txt').open().read()
    config["${complete}"] = (config_dir / 'complete.txt').open().read()
    with open('./templates/journal_entry_template.txt') as template_file:
        entry = template_file.read()
    # use these three lines to do the replacement
    rep = dict((re.escape(k), str(v)) for k, v in config.items())
    pattern = re.compile("|".join(rep.keys()))
    journal_entry = pattern.sub(lambda m: rep[re.escape(m.group(0))], entry)

    modifiers = generate_modifiers(config)
    localization = generate_localization(config)
    notification = generate_notification(config)

    return journal_entry, events, modifiers, localization, notification


import json

with open('generator_config.json') as json_file:
    configs = json.load(json_file)

journal_entrys = []
events = []
modifiers = []
localization = []
notifications = []
for entry in configs:
    journal_entry, event, modifier, local, notif = generate_journal_entry(
        entry)
    if not DEBUG and ("TODO" in journal_entry or "TODO" in event or "TODO"
                      in modifier or "TODO" in local or "TODO" in notif):
        continue
    journal_entrys.append(journal_entry)
    events.append(event)
    modifiers.append(modifier)
    localization.append(local)
    notifications.append(notif)

shutil.rmtree('./Inventions', ignore_errors=True)
Path('./Inventions/.metadata').mkdir(parents=True, exist_ok=True)
Path('./Inventions/common/journal_entries').mkdir(parents=True, exist_ok=True)
Path('./Inventions/common/modifiers').mkdir(parents=True, exist_ok=True)
Path('./Inventions/common/notification_types').mkdir(parents=True,
                                                     exist_ok=True)
Path('./Inventions/events').mkdir(parents=True, exist_ok=True)
Path('./Inventions/localization/english').mkdir(parents=True, exist_ok=True)
with open(
        'Inventions/common/journal_entries/inventionsmod_journal_entries.txt',
        'w',
        encoding='utf-8-sig') as test:
    test.writelines(journal_entrys)
with open('Inventions/events/inventionsmod_events.txt',
          'w',
          encoding='utf-8-sig') as test:
    test.write('namespace = invention_events\n\n')
    for set in events:
        test.writelines(set)
with open('Inventions/common/modifiers/inventionsmod_modifiers.txt',
          'w',
          encoding='utf-8-sig') as test:
    test.writelines(modifiers)
with open('Inventions/localization/english/inventionsmod_l_english.yml',
          'w',
          encoding='utf-8-sig') as test:
    test.write('l_english:\n')
    test.write(' event_completion_default:0 "Onwards, into the future!"\n')
    test.write(
        ' event_completion_sharing:0 "And we should share this innovation! For glory!"\n'
    )
    test.write('\n')
    test.writelines(localization)
with open(
        'Inventions/common/notification_types/inventionsmod_notifications.txt',
        'w',
        encoding='utf-8-sig') as test:
    test.writelines(notifications)

metadata = {
    "name": "Inventions",
    "id": "Inventions",
    "version": "0.0.1",
    "supported_game_version": "1.0.*",
    "short_description": "Vicky 2 style inventions",
    "tags": ["Expansion"],
    "relationships": [],
    "game_custom_data": {
        "multiplayer_synchronized": True
    }
}
with open('./inventions/.metadata/metadata.json', 'w') as metadata_file:
    json.dump(metadata, metadata_file)