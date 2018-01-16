#!/usr/bin/env python3
import re, os, json


def _extract_translation_strings(file_path):
    'Extracts the translations from the given file.'
    with open(file_path, 'r') as f:
        file_content = f.read()

    result = []
    for string in _extract_tr(file_content):
        result.append({
            'method': 'tr',
            'id': string
        })
    for item in _extract_trc(file_content):
        result.append({
            'method': 'trc',
            'hint': item['comment'],
            'id': item['id']
        })
    return result


def _extract_tr(text):
    found = re.findall('tr\(.*\)', text)
    result = []
    for tr in found:
        result.append(tr.strip()[4:-2])
    return result


def _extract_trc(text):
    found = re.findall('trc\(.*\)', text)
    result = []
    for trc in found:
        all_strings = re.findall('"(.*?)"|\'(.*?)\'', trc)
        result.append({
            'comment': all_strings[0][1],
            'id': all_strings[1][1]
        })
    return result


def _read_translations(dir_path):
    'Reads the existing json translations as a dictionary.'
    result = {}
    if (os.path.exists(dir_path)):
        for file_name in os.listdir(dir_path):
            splitted = file_name.split('.')
            file_path = os.path.join(dir_path, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    result[splitted[0]] = json.load(f)
    else:
        os.makedirs(dir_path)
    return result


def _add_missing_translations(translation_map, locale_list):
    for locale in locale_list:
        if locale not in translation_map:
            translation_map[locale] = {}
    return translation_map


def _fill_translation_maps(translations, new_translations):
    for key, value in translations.items():
        _fill_translation_map(value, new_translations)
    return translations
        

def _fill_translation_map(translation_map, new_translations):
    for key in new_translations:
        if key['id'] not in translation_map:
            translation_map[key['id']] = None
    return translation_map


def _write_translations(translations, dir_path):
    for key, value in translations.items():
        with open(os.path.join(dir_path, key + '.json'), 'w') as f:
            json.dump(value, f, indent=2, ensure_ascii=False, sort_keys=True)


def _update_translations_for_template(template_path, translation_path, locales):
    translation_map = _read_translations(translation_path)
    translation_map = _add_missing_translations(translation_map, locales)

    new_translations = _extract_translation_strings(template_path)
    complete_translation_map = _fill_translation_maps(translation_map, new_translations)
    _write_translations(complete_translation_map, translation_path)


def update_translations(base_dir, translation_path='i18n', template_path='data/templates'):
    # create locale list from pos
    locales = [x.split(".")[0] for x in os.listdir(os.path.join(base_dir, "locale")) if os.path.isdir(os.path.join(base_dir, "locale", x))]
    locales.append("en")
    for template_file_name in os.listdir(os.path.join(base_dir, template_path)):

        splitted = template_file_name.split(".")
        type = splitted.pop()
        name = ".".join(splitted)
        if type == 'json':
            new_template_path = os.path.join(base_dir, template_path, template_file_name)
            new_translation_path = os.path.join(base_dir, template_path, translation_path, name)
            _update_translations_for_template(new_template_path, new_translation_path, locales)


def update_in_each_subdir(base_dir):
    # update_translations
    for dir_name in os.listdir():
        if (os.path.isdir(dir_name)) and not dir_name.startswith('.'):
            os.chdir(dir_name)
            update_translations(base_dir)
            os.chdir('..')


if __name__ == "__main__":
    update_translations(os.path.join(".", "src", "gosa", "backend"))
