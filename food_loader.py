import xml.etree.ElementTree as ET

def load_foods(path="data/sample_foods.xml"):
    tree = ET.parse(path)
    root = tree.getroot()

    foods = []
    food_id = 1

    # Loop over each category (fruit, vegetable, grain, dairy)
    for food in root:
        foods.append({
            "id": food_id,
            "name": food.find("name").text,
            "calories": int(food.find("calories").text),
            "category": food.tag  # fruit, vegetable, etc.
        })
        food_id += 1

    return foods