import xml.etree.ElementTree as ET

def load_users(path):
    tree = ET.parse(path)
    root = tree.getroot()

    users = []

    for user in root.findall("user"):
        users.append({
            "id": int(user.find("id").text),
            "name": user.find("name").text,
            "age": int(user.find("age").text),
            "gender": user.find("gender").text,
            "weight": int(user.find("weight").text),
            "height": int(user.find("height").text),
            "daily_calories": int(user.find("daily_calories").text),
            "allergies": [allergy.text for allergy in user.findall("allergies/allergy")],
            "dietary_restrictions": [restriction.text for restriction in user.findall("dietary_restrictions/restriction")],
            "cooking_skill": int(user.find("cooking_skill").text),
            "preferred_cuisines": [cuisine.text for cuisine in user.findall("preferred_cuisines/cuisine")]
        })

    return users
