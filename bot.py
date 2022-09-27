import os, re, discord, json, requests, time
from dotenv import load_dotenv
from fuzzywuzzy import fuzz, process
from discord.utils import get
from bs4 import BeautifulSoup

from graphqlclient import GraphQLClient

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OCR = os.getenv('OCR_SPACE')
intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)

def roles(ctx):
    i = 0
    roleList = []
    for r in ctx.guild.roles:        
        roleList.append([r.name, r.id])
        i+=1
    return roleList

def fighterRoles(ctx):
    allRoles = roles(ctx)
    availableRoles = []
    for i in range(len(allRoles)):
        roleNameSplit = allRoles[i][0].lower().split(" ")
        if roleNameSplit[len(roleNameSplit)-1] == "fighters":
            availableRoles.append(allRoles[i])
    return availableRoles

async def iam(message, amNot=False):
        availableRoles = fighterRoles(message.author)
        messageSplit = message.content.split(" ")
        if len(messageSplit) == 1:
            return "Requires a role"
        del messageSplit[0]
        roleList = " ".join(messageSplit).split(",")
        checkedRoleList = []
        key = {}
        for i in range(len(availableRoles)):
            checkedRoleList.append(availableRoles[i][0])
            current = len(checkedRoleList) - 1
            checkedRoleList[current] = checkedRoleList[current].lower().replace("fighters", "").strip()
            key[checkedRoleList[current]] = availableRoles[i]
        if amNot == False:
            returnString = "Roles Given: "
        elif amNot == True:
            returnString = "Roles Removed: "
        setFlag = 0
        for i in range(len(roleList)):
            roleList[i] = roleList[i].lower().replace("fighters", "").replace("fighter", "").strip()
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



async def handleMessage(message):
    command = message.content.split(" ")[0]
    command = command.lower()
    if command == "!roles":
        availableRoles = fighterRoles(message.author)
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

#@client.event
#async def on_reaction_add(reaction, user):
#    if reaction.me and reaction.count == 1:
#        return
#    if reaction.message.author == client.user:
#        if str(reaction.emoji) == "\u23e9":
#           operation = "+"
#        elif str(reaction.emoji) == "\u23ea":
#            operation = "-"
#        else:
#            return
#        await search.handleIncrement(reaction, operation, user)

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
