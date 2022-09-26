import os, re, discord
from dotenv import load_dotenv
from fuzzywuzzy import fuzz, process
from discord.utils import get

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


async def handleMessage(message):
    print(message.content)
    command = message.content.split(" ")[0]
    command = command.lower()
    if command == "!roles":
        availableRoles = fighterRoles(message.author)
        returnStr = " \nAvailable Roles Are: "
        for i in range(len(availableRoles)):
            returnStr += "\n" + availableRoles[i][0]
        return returnStr
    if command == "!iam":
        availableRoles = fighterRoles(message.author)
        messageSplit = message.content.split(" ")
        if len(messageSplit) == 1:
            return "Requires a role"
        del messageSplit[0]
        roleList = " ".join(messageSplit).split(",")
        print(roleList)
        checkedRoleList = []
        key = {}
        for i in range(len(availableRoles)):
            checkedRoleList.append(availableRoles[i][0])
            current = len(checkedRoleList) - 1
            checkedRoleList[current] = checkedRoleList[current].lower().replace("fighters", "").strip()
            key[checkedRoleList[current]] = availableRoles[i]
        returnString = "Roles Given: "
        for i in range(len(roleList)):
            roleList[i] = roleList[i].lower().replace("fighters", "").replace("fighter", "").strip()
            matchCheck = process.extract(roleList[i], checkedRoleList, scorer=fuzz.ratio)
            print(matchCheck)
            bestFit = key[matchCheck[0][0]]
            if matchCheck[0][1] > 80:
                await message.author.add_roles(message.guild.get_role(bestFit[1]))
                returnString += bestFit[0] + ", "
        return returnString
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
    for r in message.author.guild.roles:
        print(r.name + " - " + str(r.id))
    #print(roles(message.author))
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
