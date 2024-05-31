import os


def get_anime_name():
    anime_file = 'anime_name.txt'
    if os.path.exists(anime_file):
        with open(anime_file, 'r') as file:
            anime_name = file.read().strip()
    else:
        anime_name = input("Enter Anime Name: ").strip()
        with open(anime_file, 'w') as file:
            file.write(anime_name)
    return anime_name
