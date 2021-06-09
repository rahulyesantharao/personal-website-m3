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
            for clas in classes:

                def extract(idx):
                    return clas[idx] if idx < len(clas) else ""

                class_number = extract(0)
                class_name = extract(1)
                class_proj_link = extract(2)
                class_role = extract(3)

                class_txt = (
                    f"[{class_role}] {class_number}" if class_role else class_number
                )

                ret += f'<li><a href="http://student.mit.edu/catalog/search.cgi?search={class_number}">{class_txt}</a> - {class_name}'
                if class_proj_link:
                    ret += f" (<a href={class_proj_link}>project</a>)"
                ret += "</li>"
            ret += "</ul>"
    return ret
