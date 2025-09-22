import os, re, discord, json, requests, time, asyncio
import random
from dotenv import load_dotenv
from fuzzywuzzy import fuzz, process
from discord.utils import get
from bs4 import BeautifulSoup

#from graphqlclient import GraphQLClient

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OCR = os.getenv('OCR_SPACE')
intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "db.json")

async def changeRole(message, user, emoji, remove = False):
    print(emoji)
    with open(json_path, 'r') as file:
        data = json.load(file)
    for role, stored_emoji in data[str(message.guild.id)]['roles'].items():
        #try:
        if emoji.name in stored_emoji:
            if remove == False:
                return await user.add_roles(get(message.guild.roles, id=int(role)))
            elif remove == True:
                return await user.remove_roles(get(message.guild.roles, id=int(role)))


async def addRole(message):
    role_id = message.content.split(' ', 1)[1].replace("<@&", "").replace(">", "")
    role = discord.utils.get(message.guild.roles, id=int(role_id))
    if role == None:
        return "Argument must be a tagged role."
    await message.channel.send("React to this message with the emoji you would like to use for the <@&"+role_id+"> role")
    react, user = await client.wait_for('reaction_add')

    try:
        emoji_data = "<:" + react.emoji.name + ":" + str(react.emoji.id) + ">"
    except:
        emoji_data = react.emoji
    update_result = updateRole(message.guild.id, role_id, emoji_data)
    if update_result == -1:
        return "The emoji is already in use."
    role_post = await updateRolePost(message)
    updateDBEntry(message, 'role_post', role_post.id)
   
async def updateRolePost(message):
    message_id = fetchDB(message, 'role_post')
    channel_id = fetchDB(message, 'role_channel')
    channel = message.guild.get_channel(int(channel_id))
    roles = fetchDB(message)['roles']
    new_message = "React here to set your roles. Available roles:\n"
    print(roles)
    for role, emoji in roles.items():
        new_message = new_message+"<@&" + role + ">:" + emoji + "\n"
    try:
        role_message = await channel.fetch_message(int(message_id))
        await role_message.edit(content=new_message)
    except:
        role_message = await channel.send(new_message)
    for role, emoji in roles.items():
        await role_message.add_reaction(emoji)
    return role_message


def isAdmin(message):
    try:
        with open(json_path, "r") as file:
            data = json.load(file)
        admin_role = data[str(message.guild.id)]['admin_role']
    except:
        return -1
    for role in message.author.roles:
        if str(role.id) == str(admin_role):
            return True
    return False

def fetchDB(message, key=None):
    try:
        with open(json_path, "r") as file:
            data = json.load(file)
        if key == None:
            return data[str(message.guild.id)]
        else:
            return data[str(message.guild.id)][key]
    except:
        return -1


def updateRole(server_id, new_role, new_emoji):
    with open(json_path, "r") as file:
        data = json.load(file)
    for role, emoji in data[str(server_id)]['roles'].items():
        if emoji == new_emoji and str(role) != new_role:
            return -1
    data[str(server_id)]['roles'][new_role] = new_emoji
    print(data[str(server_id)])
    with open(json_path, "w") as file:
        json.dump(data, file)

def updateDB(jsonData):
    try:
        open(json_path, "x")
    except:
        print("file exists")
    with open(json_path, "r") as file:
        try:
            data = json.load(file)
        except:
            data = {}
    server_id = str(jsonData['server'])
    del jsonData['server']
    print(server_id in data.keys() and jsonData['keep_roles'] == True)
    if server_id in data.keys() and jsonData['keep_roles'] == True:
        for key in jsonData.keys():
            if key not in ['keep_roles', 'roles']:
                data[server_id][key] = jsonData[key]
        redundantKeys=[]
        for key in data[server_id]:
            if key not in jsonData.keys():
                redundantKeys.append(key)
        for i in range(len(redundantKeys)):
            if redundantKeys[i] != 'roles':
                del data[server_id][redundantKeys[i]]
        if 'roles' not in data[server_id].keys():
            data[server_id]['roles'] = {}
    else:
        jsonData['roles'] = {}
        data[server_id] = jsonData
    with open(json_path, "w") as file:
        print(data)
        json.dump(data, file)

def updateDBEntry(message, key, value):
    with open(json_path, "r") as file:
        data = json.load(file)
    try:
        data[str(message.guild.id)][key] = value
    except:
        return -1
    with open(json_path, "w") as file:
        json.dump(data, file)
    return 1

async def yesno(channel, message_content):
    def react_check(reaction, user):
        return str(reaction.emoji) in ["\U00002705", "\U0000274c"]

    bot_msg = await channel.send(message_content)
    await bot_msg.add_reaction("\U00002705")
    await bot_msg.add_reaction("\U0000274c")
    try:
        react, user = await client.wait_for('reaction_add', check = react_check)
        if react.emoji == "\U00002705":
            return True
        else:
            return False
    except asyncio.TimeoutError:
        await msg.channel.send("You did not react within 60 seconds.")
        return -1


async def setup(message):
    bot_msg = await message.channel.send("Reply to this message with the role which should be considered admin.")
    def check(m):
        if m.reference is not None:
            return m.reference.message_id == bot_msg.id
    jsonData = {
            "server":           message.guild.id,
            "keep_roles":       1
            }
    while True:
        msg = await client.wait_for('message', check=check)
        role_id=msg.content.replace("<@&", "").replace(">", "")
        try:
            role = discord.utils.get(message.guild.roles, id=int(role_id))
            if role != None:
                jsonData['admin_role'] = role_id
                break
        except:
            print(-1)
        bot_msg = await message.channel.send("Reply to this message with ONLY a linked role, to be used as admin.")
    await msg.channel.send("Admin set to <@&"+role_id+">")
    react_mode = await yesno(msg.channel, "Use bot in react mode, or auto mode? react ✅ for react, or ❌ for auto.")
    if react_mode == -1:
        return
    elif react_mode == True:
        jsonData['type'] = 'react'
        keep_roles = await yesno(msg.channel, "Keep any existing roles?")
        if keep_roles == -1:
            return
        else:
            jsonData['keep_roles'] = keep_roles
        bot_msg = await msg.channel.send("Reply to this message with the channel to be used as the role channel.")
        while True:
            msg = await client.wait_for('message', check=check)
            channel_id = msg.content.replace("<#", "").replace(">", "")
            try:
                channel = discord.utils.get(message.guild.channels, id=int(channel_id))
                if channel != None:
                    jsonData['role_channel'] = channel_id
                    break
            except:
                print(-1)
            bot_msg = await message.channel.send("Reply to this message with ONLY a linked channel, to be used as the role channel.")
        await message.channel.send("Creating role post in <#"+channel_id+">")
        msg = await updateRolePost(message)
        jsonData['role_post'] = msg.id
    else:
        jsonData['type'] = 'auto'
        bot_msg = await updateRolePost(message)
        jsonData['role_post'] = bot_msg.id
        msg = await client.wait_for('message', check=check)
        jsonData['suffix'] = msg.content
    updateDB(jsonData)

def roles(ctx):
    i = 0
    roleList = []
    for r in ctx.guild.roles:        
        roleList.append([r.name, r.id])
        i+=1
    return roleList

def fighterRoles(message):
    allRoles = roles(message.author)
    suffix = fetchDB(message, 'suffix')
    availableRoles = []
    for i in range(len(allRoles)):
        roleNameSplit = allRoles[i][0].lower().split(" ")
        if roleNameSplit[len(roleNameSplit)-1] == suffix:
            availableRoles.append(allRoles[i])
    return availableRoles

async def iam(message, amNot=False):
        if fetchDB(message, 'type') != 'auto':
            return "Bot running in react mode."
        availableRoles = fighterRoles(message)
        messageSplit = message.content.split(" ")
        if len(messageSplit) == 1:
            return "Requires a role"
        del messageSplit[0]
        roleList = " ".join(messageSplit).split(",")
        checkedRoleList = []
        key = {}
        suffix = fetchDB(message, 'suffix')
        if suffix == -1:
            return "run !setup"
        for i in range(len(availableRoles)):
            checkedRoleList.append(availableRoles[i][0])
            current = len(checkedRoleList) - 1
            checkedRoleList[current] = checkedRoleList[current].lower().replace(suffix, "").strip()
            key[checkedRoleList[current]] = availableRoles[i]
        if amNot == False:
            returnString = "Roles Given: "
        elif amNot == True:
            returnString = "Roles Removed: "
        setFlag = 0
        for i in range(len(roleList)):
            roleList[i] = roleList[i].lower().replace(suffix, "").replace("fighter", "").strip()
            roleList[i] = roleList[i].replace("sfiv", "sf4").replace("sf5", "sfv")
            matchCheck = process.extract(roleList[i], checkedRoleList, scorer=fuzz.ratio)
            bestFit = key[matchCheck[0][0]]
            if matchCheck[0][1] > 80:
                if amNot == False:
                    await message.author.add_roles(message.guild.get_role(bestFit[1]))
                elif amNot == True:
                    await message.author.remove_roles(message.guild.get_role(bestFit[1]))
                setFlag = 1
                returnString += bestFit[0] + ", "
        if setFlag == 1:
            return returnString
        else:
            return

def getNextEvents(callType=0):
    if callType not in [0,1,2]:
        callType = 0
    phaseId = 123456
    #sheetsKey = 'YOUR_SHEETS_KEY'
    authToken = os.getenv('STARTGG_TOKEN')
    apiVersion = 'alpha'
    toID = "0f5d35a8"

    client = GraphQLClient('https://api.start.gg/gql/' + apiVersion)
    client.inject_token('Bearer ' + authToken)

    result = client.execute('''
    query TournamentsByOwner($perPage: Int!, $ownerId: ID!) {
        tournaments(query: {
            perPage: $perPage
            filter: {
                ownerId: $ownerId
            }
        }) {
        nodes {
            id
            name
            slug
            startAt
        }
      }
    }''',
    {
      "ownerId": int(os.getenv('SMBF_ID')),
      "perPage": 4
    })
    resData = json.loads(result)
    outputString = ""
    for event in reversed(resData['data']['tournaments']['nodes']):
        if time.time() > event['startAt']:
            continue
        if callType == 2:
            if "sodium showdown" not in event['name'].lower():
                continue
        outputString += event['name'] + "\nhttp://smash.gg/" + event['slug'] + "\n \n"
        if callType == 1:
            break
    if callType == 2 and outputString == "":
        outputString == "No date announced for next Sodium yet!"
    return outputString

def randomStreetFighter():
    sfgames = [
            "Street Fighter 1",
            "Street Fighter 2: Hyper Fighting",
            "Super Street Fighter 2: Turbo",
            "Street Fighter Alpha 1",
            "Street Fighter Alpha 2",
            "Street Fighter Alpha 3",
            "Street Fighter 3: New Generation",
            "Street Fighter 3: Second Impact",
            "Street Fighter 3: Third Strike",
            "Ultra Street Fighter 4: Edition Select",
            "Street Fighter V (Cringe)",
            "Street Fighter 6"
        ]
    return sfgames[random.randint(0, len(sfgames)-1)]

async def handleMessage(message):
    command = message.content.split(" ")[0]
    command = command.lower()
    if command == "!addrole":
        if fetchDB(message, "type") == "auto":
            return "Bot running in Auto mode. Please run !setup to change"
        admin = isAdmin(message)
        if admin == True:
            if len(message.content.split(" ")) != 2:
                return "Requires a single role as argument."
            return await addRole(message)
        elif admin == -1:
            return "Bot has not been set up."
        else:
            return "Not Admin."
    if command == "!test":
        print(isAdmin(message))
    if command == "!setup":
        if isAdmin(message) != False:
            return await setup(message)
        else:
            await message.channel.send("Not admin.")
    if command == "!roles":
        if fetchDB(message, 'type') != "auto":
            return "Bot running in react mode."
        availableRoles = fighterRoles(message)
        returnStr = " \nAvailable Roles Are: "
        for i in range(len(availableRoles)):
            returnStr += "\n" + availableRoles[i][0]
        return returnStr
    if command == "!iam":
        return await iam(message)
    if command in ["!iamn", "!iamnot"]:
        return await iam(message, True)
    if command == "!nextevents":
        return getNextEvents()
    if command == "!nextevent":
        return getNextEvents(1)
    if command in ["!sodium", "!nextsodium"]:
        return getNextEvents(2)
    if command == "!hi":
        return "https://c.tenor.com/odArHt0HeUwAAAAd/street-fighter-dan-hibiki.gif"
    if command == "!rsf":
        return randomStreetFighter()
    return

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    #await client.change_presence(activity=discord.Game(name="shid and fard all over the place"))
    
@client.event    
async def on_message(message):
    if message.author == client.user:
        return
    #handleMessage(message)
    response = await handleMessage(message)
    if response != "" and response != None:
        await message.channel.send(response)
    #else:
    #    return
    return

@client.event
async def on_raw_reaction_add(payload):
    guild = await client.fetch_guild(payload.guild_id)
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = await guild.fetch_member(payload.user_id)
    if user != client.user:
        if message.id == fetchDB(message, 'role_post'):
            await changeRole(message, user, payload.emoji)

@client.event
async def on_raw_reaction_remove(payload):
    guild = await client.fetch_guild(payload.guild_id)
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = await guild.fetch_member(payload.user_id)
    if user != client.user:
        if message.id == fetchDB(message, 'role_post'):
            await changeRole(message, user, payload.emoji, True)


#@client.event
#async def on_message_edit(before, after):
#    if after.author == client.user:
#        return
#    else:
#        await search.editQuery(after)
#    return

#@client.event
#async def on_message_delete(message):
#    await trophyProcess("delete", message)

client.run(TOKEN)
