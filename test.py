from pprint import pprint
import requests
from urllib.parse import urljoin
import csv
import difflib
from PIL import Image, ImageFile
import io
import numpy as np
import cv2
import random

username = 'pmkd42'
token = '719a6f7bf0fb4d1f6decb1bf847ca07720e6b4fe'
pythonanywhere_host = "www.pythonanywhere.com"
api_base = "https://{pythonanywhere_host}/api/v0/user/{username}/".format(
    pythonanywhere_host=pythonanywhere_host,
    username=username,
)
api_token = token
raw_csv_file_path = "pvp_habba.csv"
playerdb = []
playerlist = []

def get_raw_db():
    resp = requests.get(
        urljoin(api_base, "files/path/home/{username}/pvp_habba.csv".format(username=username)),
        headers={"Authorization": "Token {api_token}".format(api_token=api_token)}
    )                      
    print(resp.content)
    with open('pvp_habba.csv', 'wb') as f:
        f.write(resp.content)

def make_own_db():
    playerdb = []
    playerlist = []
    with open(raw_csv_file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            playerdb.append(row)
    #remove dupes    
    last_occurrences = {}

    for i in range(len(playerdb) - 1, -1, -1):
        entry = playerdb[i]
        key = entry[0]
        
        if key not in last_occurrences and key is not '':
            last_occurrences[key] = entry
        
    playerdb = list(last_occurrences.values())
    #player list
    playerlist = []
    for entry in playerdb:
        playerlist.append(entry[0])


    #format for image
    purified_playerdb = []
    with open("pokemon_list_file.csv", 'r') as file:
        csv_reader = csv.reader(file)
        pokemon_list = [row[0] for row in csv_reader]
        
    for entry in playerdb:
        purified_entry = entry.copy()
        for i in range(1, 7):
                field = purified_entry[i]
                if any(qualifier in field for qualifier in ['galar', 'galarian', 'alola', 'alolan', 'hisui', 'hisuian']):
                    field = field.replace('galar', '').replace('galarian', '').replace('alola', '').replace('alolan', '').replace('hisui', '').replace('hisuian', '')
                    field = field.replace('_','').replace(' ','')

                matched_pokemon = difflib.get_close_matches(field, pokemon_list, n=1, cutoff=0.5)

                if matched_pokemon:
                    temp = matched_pokemon[0]
                    if 'galar' in purified_entry[i] or 'Galar' in purified_entry[i]:
                        field = temp + '-galarian'
                    elif 'alola' in purified_entry[i] or 'Alola' in purified_entry[i]:
                        field = temp + '-alolan'
                    elif 'hisui' in purified_entry[i] or 'Hisui' in purified_entry[i]:
                        field = temp + '-hisuian'
                    else:
                        field = temp
                purified_entry[i] = field.lower()
        purified_playerdb.append(purified_entry)
    playerdb = purified_playerdb
    #write playerdb and playerlist locally
    with open("playerlist.csv", 'w', newline='') as file:
        writer = csv.writer(file)
        for item in playerlist:
            writer.writerow([item])
    with open("playerdb.csv", 'w', newline='') as file2:
        writer = csv.writer(file2)
        for item in playerdb:
            writer.writerow([item])
    return playerdb, playerlist

def generate_image(names):
    header_text = names[0]
    image_urls = names[1:7]
    to_send = 1
    images = []
    for url in image_urls:
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        image_url = "https://img.pokemondb.net/sprites/sword-shield/icon/" + url + ".png"
        response = requests.get(image_url)
        #image = Image.open(io.BytesIO(response.content))
        if response.status_code == 200:
            with open(url+'.png', "wb") as f:
                f.write(response.content)
                print(f"Image saved as {url}")
                images.append(url+'.png')
        else:
            print("Failed to download the image")
    pngs = list(map(lambda x: cv2.imread(x), images))
    res_img = cv2.hconcat(pngs)
    cv2.imwrite(header_text+".png",res_img)

    #send to cloud
    img_path = header_text + ".png"
    team_path = "files/path/home/{username}/PoGoblr/static/".format(username=username) + header_text + ".png"
    resp = requests.post(
    urljoin(api_base, team_path),
    headers={"Authorization": "Token {api_token}".format(api_token=api_token)},
    files={'content': open(img_path, 'rb')})
    print(resp.status_code)


def generate_random_pairs(csv_file):
    players = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            players.append(row[0])

    num_players = len(players)
    random.shuffle(players)

    pairs = []
    for i in range(0, num_players - 1, 2):
        pairs.append((players[i], players[i+1]))

    # If there is an odd number of players, one player gets paired against themselves
    if num_players % 2 != 0:
        pairs.append((players[-1], players[-1]))
    #write to file
    with open("matchups.csv", 'w', newline='') as file:
        writer = csv.writer(file)
        for item in pairs:
            writer.writerow(item)
    #send to cloud
    csv_path = "matchups.csv"
    team_path = "files/path/home/{username}/PoGoblr/".format(username=username) + "matchups.csv"
    resp = requests.post(
    urljoin(api_base, team_path),
    headers={"Authorization": "Token {api_token}".format(api_token=api_token)},
    files={'content': open(csv_path, 'rb')})
    print(resp.status_code)

    return pairs



#main
get_raw_db()
playerdb, playerlist = make_own_db()
print(playerdb)
for i in playerdb:
    generate_image(i)
random_pairs = generate_random_pairs("playerlist.csv")
for pair in random_pairs:
    print(pair)

