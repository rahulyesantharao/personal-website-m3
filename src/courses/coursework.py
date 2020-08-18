import json


def get_semester_emoji(semester):
    emoji = ""
    if "Spring" in semester:
        emoji = "🌼"
    elif "IAP" in semester:
        emoji = "❄️"
    elif "Fall" in semester:
        emoji = "🍂"
    return emoji


def func():
    ret = ""
    with open("./coursework.json", "r") as f:
        data = json.load(f)
        for (semester, classes) in data:
            ret += f"<h3>{get_semester_emoji(semester)} {semester}</h3>"
            ret += "<ul>"
            for (class_number, class_name, class_proj_link) in classes:
                ret += f'<li><a href="http://student.mit.edu/catalog/search.cgi?search={class_number}">{class_number}</a> - {class_name}'
                if class_proj_link:
                    ret += f" (<a href={class_proj_link}>project</a>)"
                ret += "</li>"
            ret += "</ul>"
    return ret
