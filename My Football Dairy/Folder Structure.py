# Directory structure generator for the football tracker app
import os

folders = [
    "screens",
    "assets/images",
    "assets/fonts",
    "data",
    "models",
    "utils"
]

files = {
    "screens": [
        "login_screen.py",
        "home_screen.py",
        "team_screen.py",
        "player_screen.py",
        "comparison_screen.py",
        "add_match_screen.py"
    ],
    "data": [
        "database.py",
        "sample_data.json"
    ],
    "models": [
        "player_model.py",
        "team_model.py",
        "match_model.py"
    ],
    "utils": [
        "helpers.py",
        "validators.py"
    ]
}

def create_structure():
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Created folder: {folder}")

    for folder, file_list in files.items():
        for file in file_list:
            path = os.path.join(folder, file)
            with open(path, 'w') as f:
                f.write("# " + file)
            print(f"Created file: {path}")

if __name__ == '__main__':
    create_structure()
